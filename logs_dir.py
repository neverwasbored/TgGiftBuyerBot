# create_logs_dir.py
import os

# Создаём директорию logs если её нет
if not os.path.exists('logs'):
    os.makedirs('logs')
    print("✅ Created 'logs' directory")
else:
    print("📁 'logs' directory already exists")

# Или добавьте в main.py перед запуском бота:
