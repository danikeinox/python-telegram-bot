import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, ApplicationBuilder, InlineQueryHandler

# Importar Firebase Admin y las credenciales
import firebase_admin
from firebase_admin import auth, credentials

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

# Función para iniciar sesión automáticamente en Firebase
def iniciar_sesion_firebase(user_id: int, user_name: str) -> str:
    # Crear el usuario en Firebase Authentication
    try:
        user = auth.create_user(
            uid=str(user_id),
            display_name=user_name,
            email=f'{user_id}@telegram.bot',  # Correo ficticio para evitar conflictos
            password=None  # No se necesita contraseña si usamos Telegram
        )
        return user.uid  # Devolver el UID del usuario creado
    except Exception as e:
        logging.error(f'Error al crear usuario en Firebase: {str(e)}')
        return None

# Comando /start para iniciar sesión y enviar a la página
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name

    # Iniciar sesión en Firebase
    firebase_uid = iniciar_sesion_firebase(user_id, user_name)

    if firebase_uid:
        update.message.reply_text(f'Bienvenido, {user_name}! Tu sesión ha sido iniciada automáticamente.')
        # Aquí puedes redirigir al usuario a la página web con la sesión activa
        # Por ejemplo, enviar un enlace a la página web con el UID del usuario como parámetro
        # Ejemplo: update.message.reply_text(f'Puedes acceder a la página aquí: https://miweb.com?uid={firebase_uid}')
    else:
        update.message.reply_text('Ocurrió un error al iniciar sesión. Por favor, inténtalo de nuevo más tarde.')

async def unknown(update: Update, context: CallbackContext):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Lo siento, no entendí ese comando.")

if __name__ == '__main__':
    # Obtener el token del archivo .env
    TOKEN = os.getenv('BOT_TOKEN')

    # Crear la aplicación con el token cargado desde el archivo .env
    application = ApplicationBuilder().token(TOKEN).build()

    # Definir los handlers
    start_handler = CommandHandler('start', start)
    unknown_handler = InlineQueryHandler(unknown)

    # Agregar los handlers a la aplicación
    application.add_handler(start_handler)
    application.add_handler(unknown_handler)

    # Ejecutar la aplicación
    application.run_polling()
