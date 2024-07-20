import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, ApplicationBuilder, InlineQueryHandler

# Importar Firebase Admin y las credenciales
import firebase_admin
from firebase_admin import auth, credentials, firestore

# Configurar el logger
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Inicializar Firebase Admin
firebase_cred_path = os.getenv('FIREBASE_SERVICE_ACCOUNT')

if firebase_cred_path:
    cred = credentials.Certificate(firebase_cred_path)
    firebase_admin.initialize_app(cred)
    logging.info('Firebase inicializado correctamente con las credenciales proporcionadas.')
else:
    raise ValueError('La ruta a las credenciales de Firebase no está configurada correctamente en el archivo .env')

# Obtener el token del archivo .env
TOKEN = os.getenv('BOT_TOKEN')

# Función para manejar el comando /start
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name

    # Iniciar sesión en Firebase y guardar/actualizar datos en Firestore
    firebase_uid = iniciar_sesion_firebase(user_id, user_name)

    if firebase_uid:
        await update.message.reply_text(text=f'Bienvenido, {user_name}! Tu sesión ha sido iniciada automáticamente.')
        # Aquí puedes redirigir al usuario a la página web con la sesión activa
        # Por ejemplo, enviar un enlace a la página web con el UID del usuario como parámetro
        # Ejemplo: await update.message.reply_text(f'Puedes acceder a la página aquí: https://miweb.com?uid={firebase_uid}')
    else:
        await update.message.reply_text('Ocurrió un error al iniciar sesión. Por favor, inténtalo de nuevo más tarde.')

# Función para manejar el comando /play
async def play(update: Update, context: CallbackContext) -> None:
    # Obtener información del usuario de Telegram
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name

    # Crear el botón para abrir el webapp
    keyboard = [[InlineKeyboardButton("Jugar ahora", url="https://t.me/TapHeroesBot/TapHeroes")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Enviar el mensaje con el botón al usuario
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Haz clic en el siguiente botón para jugar:', reply_markup=reply_markup)


# Función para manejar comandos desconocidos
async def unknown(update: Update, context: CallbackContext):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Lo siento, no entendí ese comando.")

# Función para iniciar sesión automáticamente en Firebase
def iniciar_sesion_firebase(user_id: int, user_name: str) -> str:
    # Verificar si el usuario ya existe en Firebase Authentication
    try:
        user = auth.get_user(str(user_id))
        return user.uid  # Devolver el UID del usuario existente
    except auth.UserNotFoundError:
        # El usuario no existe, procedemos a crearlo
        try:
            user = auth.create_user(
                uid=str(user_id),
                display_name=user_name,
                email=f'{user_id}@telegram.bot',  # Correo ficticio para evitar conflictos
                password=None  # No se necesita contraseña si usamos Telegram
            )
            # Almacenar datos en Firestore
            guardar_datos_usuario(user.uid, user_name, user_id)
            return user.uid
        except Exception as e:
            logging.error(f'Error al crear usuario en Firebase: {str(e)}')
            return None
    except Exception as e:
        logging.error(f'Error al verificar usuario en Firebase: {str(e)}')
        return None

# Función para guardar datos del usuario en Firestore
def guardar_datos_usuario(uid: str, user_name: str, telegram_id: int):
    # Obtener referencia al documento del usuario en Firestore
    db = firestore.client()
    user_ref = db.collection('users').document(uid)

    # Datos a almacenar
    user_data = {
        'user_name': user_name,
        'telegram_id': telegram_id,
        'premium': False  # Por defecto, el usuario no tiene premium
    }

    # Actualizar o crear el documento en Firestore
    user_ref.set(user_data, merge=True)  # Usar merge=True para actualizar datos existentes

    logging.info(f'Datos del usuario {uid} almacenados correctamente en Firestore.')

# Crear la aplicación con el token cargado desde el archivo .env
application = ApplicationBuilder().token(TOKEN).build()

# Definir los handlers
start_handler = CommandHandler('start', start)
play_handler = CommandHandler('play', play)
unknown_handler = InlineQueryHandler(unknown)

# Agregar los handlers a la aplicación
application.add_handler(start_handler)
application.add_handler(play_handler)
application.add_handler(unknown_handler)

# Ejecutar la aplicación
application.run_polling()
