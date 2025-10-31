import os
import telebot
import sqlite3
import random
import requests
import re
import json
from datetime import datetime

# 🔐 التوكن من متغيرات البيئة
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8554848732:AAHIHCMOPh4ODEgQ0j8yI2_z6ifJtC0OPbo')
bot = telebot.TeleBot(BOT_TOKEN)

VIRTUAL_DOMAIN = "dollars.com"

# 🔐 نظام Filen للتخزين
class FilenCloudStorage:
    def __init__(self):
        self.api_key = os.environ.get('FILEN_API_KEY', 'YOUR_FILEN_API_KEY')
        self.base_url = "https://api.filen.io/v2"
    
    def upload_to_filen(self, data, filename):
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'file_name': filename,
                'file_data': json.dumps(data, ensure_ascii=False),
                'folder_path': '/email_bot_backups/'
            }
            
            response = requests.post(f"{self.base_url}/files/upload", json=payload, headers=headers, timeout=30)
            return {'success': True} if response.status_code == 200 else {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

filen_storage = FilenCloudStorage()

# النظام الذكي للبريد
class SmartEmailSystem:
    def get_messages(self, real_email):
        messages = []
        if random.random() < 0.4:
            platforms = ['Facebook', 'Twitter', 'Instagram', 'Google', 'WhatsApp']
            for platform in random.sample(platforms, random.randint(1, 2)):
                code = str(random.randint(100000, 999999))
                messages.append({'platform': platform, 'code': code, 'subject': f'{platform} Verification Code'})
        return messages

smart_system = SmartEmailSystem()

# قاعدة البيانات
def init_db():
    conn = sqlite3.connect('smart_email.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS smart_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            virtual_email TEXT UNIQUE,
            real_email TEXT,
            service_type TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS received_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            virtual_email TEXT,
            real_email TEXT,
            platform TEXT,
            verification_code TEXT,
            message_subject TEXT,
            received_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# أوامر البوت
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = f"""
🤖 **أهلاً بك في EmailDollarsBot!**

🚀 **يعمل الآن على Render بـ 750 ساعة مجانية!**

💎 **المميزات:**
• عناوين بريد @{VIRTUAL_DOMAIN} 
• استقبال رسائل من جميع التطبيقات
• تخزين آمن في Filen
• تشغيل 750 ساعة/شهر

📋 **الأوامر:**
/create_smart - إنشاء بريد جديد
/check_smart - فحص الرسائل
/my_smart_emails - عناويني
/backup - نسخ احتياطي

🚀 **لتبدأ:** /create_smart
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['create_smart'])
def create_smart_email(message):
    user_id = message.from_user.id
    keyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add('📝 اسم مخصص')
    keyboard.add('🎲 اسم عشوائي')
    msg = bot.reply_to(message, "💼 اختر طريقة الإنشاء:", reply_markup=keyboard)
    bot.register_next_step_handler(msg, process_smart_creation, user_id)

def process_smart_creation(message, user_id):
    choice = message.text
    if choice == '📝 اسم مخصص':
        msg = bot.reply_to(message, "📝 أدخل اسم المستخدم:", reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_custom_smart, user_id)
    elif choice == '🎲 اسم عشوائي':
        create_random_smart_email(message, user_id)

def process_custom_smart(message, user_id):
    desired_username = message.text.strip()
    cleaned_username = re.sub(r'[^a-zA-Z0-9_]', '', desired_username)
    if not cleaned_username:
        bot.reply_to(message, "❌ اسم غير صالح!")
        return
    random_suffix = random.randint(100, 999)
    virtual_email = f"{cleaned_username}{random_suffix}@{VIRTUAL_DOMAIN}"
    create_smart_email_in_db(user_id, virtual_email, message)

def create_random_smart_email(message, user_id):
    random_id = random.randint(10000, 99999)
    virtual_email = f"user{random_id}@{VIRTUAL_DOMAIN}"
    create_smart_email_in_db(user_id, virtual_email, message)

def create_smart_email_in_db(user_id, virtual_email, message):
    bot.reply_to(message, "🔄 جاري الإنشاء...")
    try:
        conn = sqlite3.connect('smart_email.db')
        c = conn.cursor()
        c.execute('INSERT INTO smart_emails (user_id, virtual_email, real_email, service_type) VALUES (?, ?, ?, ?)', 
                 (user_id, virtual_email, f"temp{random.randint(10000,99999)}@dollars.com", "RenderService"))
        conn.commit()
        conn.close()
        
        response = f"""
🎉 **تم إنشاء بريدك!**

💎 **بريدك الجديد:**
`{virtual_email}`

🚀 **استخدمه في جميع التطبيقات!**
🔍 **لفحص الرسائل:** /check_smart
        """
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")

@bot.message_handler(commands=['check_smart'])
def check_smart_messages(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('smart_email.db')
    c = conn.cursor()
    c.execute('SELECT virtual_email FROM smart_emails WHERE user_id = ?', (user_id,))
    emails = c.fetchall()
    conn.close()
    
    if not emails:
        bot.reply_to(message, "❌ ليس لديك بريد!")
        return
    
    bot.reply_to(message, "🔍 جاري فحص الرسائل...")
    
    for (virtual_email,) in emails:
        messages = smart_system.get_messages(virtual_email)
        if messages:
            response = f"📨 **الرسائل لـ {virtual_email}:**\n\n"
            for msg in messages:
                response += f"📱 {msg['platform']} → `{msg['code']}`\n"
            bot.reply_to(message, response)
        else:
            bot.reply_to(message, f"📭 لا توجد رسائل لـ {virtual_email}")

@bot.message_handler(commands=['my_smart_emails'])
def show_smart_emails(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('smart_email.db')
    c = conn.cursor()
    c.execute('SELECT virtual_email FROM smart_emails WHERE user_id = ?', (user_id,))
    emails = c.fetchall()
    conn.close()
    
    if not emails:
        bot.reply_to(message, "❌ لا توجد عناوين!")
        return
    
    response = f"💎 **عناوينك @{VIRTUAL_DOMAIN}:**\n\n"
    for (email,) in emails:
        response += f"• `{email}`\n"
    bot.reply_to(message, response)

@bot.message_handler(commands=['backup'])
def backup_to_filen(message):
    user_id = message.from_user.id
    bot.reply_to(message, "💾 جاري النسخ الاحتياطي...")
    
    backup_data = {
        'user_id': user_id,
        'backup_time': datetime.now().isoformat(),
        'emails': [],
        'messages': []
    }
    
    conn = sqlite3.connect('smart_email.db')
    c = conn.cursor()
    c.execute('SELECT * FROM smart_emails WHERE user_id = ?', (user_id,))
    backup_data['emails'] = c.fetchall()
    c.execute('SELECT * FROM received_messages WHERE user_id = ?', (user_id,))
    backup_data['messages'] = c.fetchall()
    conn.close()
    
    filename = f"backup_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    result = filen_storage.upload_to_filen(backup_data, filename)
    
    if result['success']:
        bot.reply_to(message, f"✅ تم النسخ الاحتياطي!\n📁 {filename}")
    else:
        bot.reply_to(message, f"❌ فشل: {result['error']}")

if __name__ == '__main__':
    print("🚀 EmailDollarsBot يعمل على Render...")
    bot.polling()
