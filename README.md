# Telegram Auction Mini-App 

Телеграм мини-приложение для создания аукционных объявлений с несколькими режимами продажи.

## 🚀 Возможности

- **Множественные режимы продажи:**
  - Фиксированная цена
  - Бесплатно
  - Назовите цену
  - Аукцион

- **Загрузка фотографий** с предпросмотром и удалением
- **Интеграция с Telegram WebApp API** для аутентификации
- **Адаптивный дизайн** для мобильных устройств
- **Сохранение черновиков** объявлений
- **3-шаговый мастер создания** объявлений

## 🛠 Технологии

**Frontend:**
- Vanilla JavaScript
- Bootstrap 5
- Telegram WebApp API
- Feather Icons

**Backend:**
- Flask
- SQLAlchemy
- PostgreSQL/SQLite
- PIL для обработки изображений

## 📦 Установка

1. Клонируйте репозиторий:
```bash
git clone <your-repo-url>
cd telegram-auction-miniapp
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте переменные окружения:
```bash
export DATABASE_URL="your_database_url"
export SESSION_SECRET="your_session_secret"  
export BOT_TOKEN="your_telegram_bot_token"
```

4. Запустите приложение:
```bash
python main.py
```

## 🔧 Конфигурация

Создайте файл `.env` с необходимыми переменными:

```
DATABASE_URL=postgresql://username:password@host:port/database
SESSION_SECRET=your-secret-key-here
BOT_TOKEN=your-telegram-bot-token
```

## 📱 Использование

1. Создайте Telegram бота через @BotFather
2. Настройте Mini App в настройках бота
3. Укажите URL вашего приложения
4. Пользователи смогут получить доступ через меню бота

## 🏗 Структура проекта

```
├── app.py              # Конфигурация Flask приложения
├── main.py             # Точка входа
├── models.py           # Модели базы данных
├── routes.py           # API маршруты
├── utils.py            # Вспомогательные функции
├── static/
│   ├── css/
│   │   └── telegram-theme.css
│   ├── js/
│   │   ├── main.js
│   │   └── telegram-webapp.js
│   └── uploads/        # Загруженные изображения
└── templates/
    ├── index.html
    ├── create_listing.html
    └── my_listings.html
```

## 💰 Валюта

Приложение использует израильские шекели (₪) с поддержкой только целых чисел.

## 🔐 Безопасность

- HMAC-SHA256 проверка данных Telegram WebApp
- Безопасная обработка загружаемых файлов
- Ограничения размера файлов (16MB)
- Защита от CSRF атак

## 📄 Лицензия

MIT License