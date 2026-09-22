import os
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# ==============================================================================
# CONFIGURACIÓN FIJA
# ==============================================================================
BOT_TOKEN = "8743901516:AAEN1tQAPEr2JKqNndOEaJT4tkMvhF_Xkeg"
CANAL_ID = -2105468272  # Tu canal fijo

# Servidor web interno obligatorio para mantener el plan gratuito de Render activo
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "🤖 Bot de duplicados activo y operando."

# Instancia del bot de Telegram
application = None

async def comando_duplicados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ **Formato incorrecto.**\nUsa: `/duplicados INICIO FIN`\nEjemplo: `/duplicados 4382 4384`",
            parse_mode="Markdown"
        )
        return

    try:
        inicio = int(args[0])
        fin = int(args[1])
    except ValueError:
        await update.message.reply_text("❌ Los números deben ser enteros.")
        return

    await update.message.reply_text(f"🔍 Analizando desde el mensaje {inicio} al {fin}...")
    print(f"\n🔍 [INICIO] Escaneando rango {inicio} al {fin} en el canal.")

    archivos_vistos = set()
    mensajes_a_borrar = []
    revisados = 0

    for msg_id in range(inicio, fin + 1):
        try:
            await asyncio.sleep(0.1)
            
            msg = await context.bot.forward_message(
                chat_id=update.effective_chat.id,
                from_chat_id=CANAL_ID,
                message_id=msg_id
            )
            
            identificador = None
            if msg.document and msg.document.file_name:
                identificador = msg.document.file_name.strip().lower()
            elif msg.audio and msg.audio.file_name:
                identificador = msg.audio.file_name.strip().lower()
            elif msg.video and msg.video.file_name:
                identificador = msg.video.file_name.strip().lower()
            elif msg.photo:
                identificador = f"foto_{msg.photo[-1].file_unique_id}"
            elif msg.video:
                identificador = f"video_{msg.video.file_unique_id}"
            elif msg.audio:
                identificador = f"audio_{msg.audio.file_unique_id}"
            elif msg.document:
                identificador = f"doc_{msg.document.file_unique_id}"

            if identificador:
                revisados += 1
                if identificador in archivos_vistos:
                    mensajes_a_borrar.append(msg_id)
                else:
                    archivos_vistos.add(identificador)

            await msg.delete()
        except Exception:
            continue

    if mensajes_a_borrar:
        borrados = 0
        for m_id in mensajes_a_borrar:
            try:
                await context.bot.delete_message(chat_id=CANAL_ID, message_id=m_id)
                borrados += 1
                await asyncio.sleep(0.3)
            except Exception:
                pass

        await update.message.reply_text(f"✅ ¡Limpieza completada!\n- Archivos revisados: {revisados}\n- Duplicados eliminados: {borrados} (se ha dejado una copia)")
    else:
        await update.message.reply_text(f"✨ Análisis finalizado. Se revisaron {revisados} elementos y no hay duplicados.")

async def main():
    global application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("duplicados", comando_duplicados))
    
    await application.initialize()
    await application.start()
    print("🤖 Bot iniciado correctamente en la nube.")
    
    # Mantiene el polling de Telegram activo en segundo plano sin bloqueos de proxy
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES, poll_interval=3.0)

if __name__ == "__main__":
    # Arrancamos el bucle de Telegram junto con Flask para Render
   asyncio.run(main())
   port = int(os.environ.get("PORT", 10000))
   app_flask.run(host="0.0.0.0", port=port)
