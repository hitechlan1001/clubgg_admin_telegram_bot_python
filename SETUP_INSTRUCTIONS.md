# Setup Instructions

## Environment Configuration

1. **Copy the environment template:**
   ```bash
   cp env_template.txt .env
   ```

2. **Edit `.env` file with your actual values:**
   ```env
   # Telegram Bot Configuration
   TELEGRAM_BOT_TOKEN=your_actual_bot_token
   AUTHORIZED_USERS=123456789,987654321

   # ClubGG Login Configuration
   UNION_LOGIN_ID=your_clubgg_username
   UNION_LOGIN_PWD=your_clubgg_password
   CAPSOLVER_API_KEY=your_capsolver_api_key
   UNION_RECAPTCHA_BACKEND=your_backend_value

   # Database Configuration
   DB_HOST=your_database_host
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_NAME=your_database_name
   DB_TABLE=chat_to_club
   ```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Database Setup

Ensure the `chat_to_club` table exists in your database:

```sql
-- The table should have this structure:
-- chat_id (BIGINT) - Telegram chat ID
-- club_id (INT) - Club display ID
-- last_sent (TIMESTAMP) - Last alert sent time
```

## Run the Bot

```bash
python main.py
```

## Configuration Details

### Database Configuration
- **Host**: Configure in `.env` file
- **Database**: Configure in `.env` file
- **Table**: `chat_to_club`
- **User**: Configure in `.env` file (read-only access recommended)

### Bot Features
- **Auto-detection**: Commands automatically detect club from chat context
- **Dynamic mapping**: Backend IDs fetched from ClubGG API
- **Alert system**: Sends alerts to specific club chats
- **Data storage**: Uses `bot_data` for mapping storage

### Commands
- `/cl` - View club limits
- `/addwl <amount>` - Add to win limit
- `/subwl <amount>` - Subtract from win limit
- `/setwl <amount>` - Set win limit
- `/addsl <amount>` - Add to loss limit
- `/subsl <amount>` - Subtract from loss limit
- `/setsl <amount>` - Set loss limit
- `/scr <amount>` - Send credits
- `/ccr <amount>` - Claim credits

## Security Notes

- Never commit the `.env` file to version control
- Keep your API keys and passwords secure
- Use read-only database access when possible
- Backend IDs are fetched dynamically from API
