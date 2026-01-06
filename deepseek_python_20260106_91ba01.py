import telebot
import subprocess
import os
import sys

# Настройки
TOKEN = "ВАШ_ТОКЕН_БОТА"  # Замените на токен от @BotFather
ALLOWED_USERS = [123456789]  # Замените на ваш ID Telegram

bot = telebot.TeleBot(TOKEN)

def run_cmd(command):
    """Выполняет команду в CMD и возвращает результат"""
    try:
        # Для Windows - выполняем через cmd.exe
        if sys.platform == 'win32':
            # Скрываем окно CMD
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # Выполняем команду
            result = subprocess.run(
                f'cmd /c "{command}"',
                shell=True,
                capture_output=True,
                text=True,
                encoding='cp866',  # Кодировка для русского текста
                timeout=30,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            # Для Linux/Mac
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
        
        return result
        
    except subprocess.TimeoutExpired:
        return type('obj', (object,), {
            'stdout': '',
            'stderr': 'Ошибка: время выполнения истекло (30 секунд)',
            'returncode': -1
        })()
    except Exception as e:
        return type('obj', (object,), {
            'stdout': '',
            'stderr': f'Ошибка выполнения: {str(e)}',
            'returncode': -1
        })()

@bot.message_handler(commands=['start', 'help'])
def start(message):
    """Начало работы"""
    help_text = """
💻 *Бот для выполнения CMD команд*

*Основные команды:*
/run <команда> - Выполнить команду в CMD
/cmd <команда> - Выполнить команду в CMD (сокращенно)

*Примеры команд:*
/run dir - Показать содержимое папки
/run ipconfig - Показать сетевые настройки
/run systeminfo - Информация о системе
/run tasklist - Список процессов
/run echo Hello World - Вывести текст

*Специальные команды:*
/pwd - Текущая рабочая папка
/cd <путь> - Сменить папку
/disk - Информация о дисках
/process - Список процессов
"""
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['run', 'cmd'])
def execute_command(message):
    """Выполняет команду в CMD"""
    # Проверяем доступ
    if message.from_user.id not in ALLOWED_USERS:
        bot.reply_to(message, "❌ *Доступ запрещен!*", parse_mode='Markdown')
        return
    
    # Получаем команду
    if len(message.text.split()) < 2:
        bot.reply_to(message, "📝 *Использование:* /run `<команда>`", parse_mode='Markdown')
        return
    
    command = ' '.join(message.text.split()[1:])
    
    # Отправляем сообщение о начале выполнения
    status_msg = bot.reply_to(message, f"⚡ *Выполняю:* `{command}`", parse_mode='Markdown')
    
    # Выполняем команду
    result = run_cmd(command)
    
    # Формируем ответ
    response = f"💻 *CMD Команда:*\n`{command}`\n\n"
    
    if result.stdout:
        # Обрезаем слишком длинный вывод
        output = result.stdout.strip()
        if len(output) > 3000:
            output = output[:3000] + "\n\n... (вывод обрезан)"
        response += f"📤 *Результат:*\n```\n{output}\n```\n"
    
    if result.stderr:
        error = result.stderr.strip()
        if len(error) > 1000:
            error = error[:1000] + "\n... (ошибки обрезаны)"
        response += f"\n⚠️ *Ошибки:*\n```\n{error}\n```\n"
    
    response += f"\n🔢 *Код выхода:* {result.returncode}"
    
    # Отправляем результат
    bot.edit_message_text(
        response,
        chat_id=message.chat.id,
        message_id=status_msg.message_id,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['pwd'])
def show_pwd(message):
    """Показывает текущую папку"""
    if message.from_user.id not in ALLOWED_USERS:
        return
    
    result = run_cmd("cd")
    if result.stdout:
        bot.reply_to(message, f"📁 *Текущая папка:*\n`{result.stdout.strip()}`", parse_mode='Markdown')

@bot.message_handler(commands=['cd'])
def change_dir(message):
    """Меняет текущую папку"""
    if message.from_user.id not in ALLOWED_USERS:
        return
    
    if len(message.text.split()) < 2:
        bot.reply_to(message, "📝 *Использование:* /cd `<путь>`", parse_mode='Markdown')
        return
    
    path = ' '.join(message.text.split()[1:])
    try:
        os.chdir(path)
        new_path = os.getcwd()
        bot.reply_to(message, f"✅ *Перешел в папку:*\n`{new_path}`", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ *Ошибка:* {str(e)}", parse_mode='Markdown')

@bot.message_handler(commands=['disk'])
def disk_info(message):
    """Информация о дисках"""
    if message.from_user.id not in ALLOWED_USERS:
        return
    
    result = run_cmd("wmic logicaldisk get size,freespace,caption")
    if result.stdout:
        bot.reply_to(message, f"💾 *Диски:*\n```\n{result.stdout.strip()}\n```", parse_mode='Markdown')

@bot.message_handler(commands=['process'])
def process_list(message):
    """Список процессов"""
    if message.from_user.id not in ALLOWED_USERS:
        return
    
    result = run_cmd("tasklist")
    if result.stdout:
        # Берем только первые 50 строк чтобы не перегружать
        lines = result.stdout.strip().split('\n')[:50]
        truncated_output = '\n'.join(lines)
        bot.reply_to(message, f"📝 *Процессы (первые 50):*\n```\n{truncated_output}\n```", parse_mode='Markdown')

@bot.message_handler(commands=['ip'])
def ip_info(message):
    """Сетевые настройки"""
    if message.from_user.id not in ALLOWED_USERS:
        return
    
    result = run_cmd("ipconfig")
    if result.stdout:
        bot.reply_to(message, f"🌐 *Сеть:*\n```\n{result.stdout[:3000]}\n```", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    """Обработчик всех сообщений"""
    if message.from_user.id in ALLOWED_USERS:
        if message.text.startswith('/'):
            bot.reply_to(message, "❓ *Неизвестная команда. Используйте /help*", parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ *Доступ запрещен!*", parse_mode='Markdown')

# Запуск бота
if __name__ == '__main__':
    print("🤖 Бот для CMD запущен!")
    print("🔧 Используйте команды в Telegram:")
    print("   /run <команда> - выполнить команду")
    print("   /help - справка")
    print("   Ctrl+C для остановки")
    
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")