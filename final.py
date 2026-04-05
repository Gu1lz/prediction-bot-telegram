from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
import asyncio
from datetime import datetime
import json
import os
from dotenv import load_dotenv
from scraper import fetch_search
from parser import parse_question
from weather import fetch_weather
from decision import best_market

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
CHECK_INTERVAL = 50
OPPORTUNITY_EXPIRY = 10
SUBSCRIBERS_FILE = "subscribers.json"
SENT_OPPORTUNITIES_FILE = "sent_opportunities.json"
class PolymarketBot:
    def __init__(self, token):
        self.app = Application.builder().token(token).build()
        self.subscribers = self.load_subscribers()
        self.sent_opportunities = self.load_sent_opportunities()
        self.is_running = False
        self.setup_handlers()
        print(f"✅ Bot initialized with {len(self.subscribers)} subscribers")
        print(f"📝 Loaded {len(self.sent_opportunities)} sent opportunities")
    def load_subscribers(self):
        """Load subscribers from file"""
        if os.path.exists(SUBSCRIBERS_FILE):
            try:
                with open(SUBSCRIBERS_FILE, 'r') as f:
                    data = json.load(f)
                    return set(data)
            except Exception as e:
                print(f"⚠️ Error loading subscribers: {e}")
        return set()
    def save_subscribers(self):
        """Save subscribers to file"""
        try:
            with open(SUBSCRIBERS_FILE, 'w') as f:
                json.dump(list(self.subscribers), f)
            print(f"💾 Saved {len(self.subscribers)} subscribers to file")
        except Exception as e:
            print(f"⚠️ Error saving subscribers: {e}")
    def load_sent_opportunities(self):
        """Load sent opportunities from file"""
        if os.path.exists(SENT_OPPORTUNITIES_FILE):
            try:
                with open(SENT_OPPORTUNITIES_FILE, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return {opp: datetime.now().timestamp() for opp in data}
                    return {k: v for k, v in data.items()}
            except Exception as e:
                print(f"⚠️ Error loading sent opportunities: {e}")
        return {}
    def save_sent_opportunities(self):
        """Save sent opportunities to file"""
        try:
            with open(SENT_OPPORTUNITIES_FILE, 'w') as f:
                json.dump(self.sent_opportunities, f)
        except Exception as e:
            print(f"⚠️ Error saving sent opportunities: {e}")
    def cleanup_old_opportunities(self):
        """Remove opportunities older than OPPORTUNITY_EXPIRY seconds"""
        current_time = datetime.now().timestamp()
        expired = []
        for opp_id, timestamp in list(self.sent_opportunities.items()):
            if current_time - timestamp > OPPORTUNITY_EXPIRY:
                expired.append(opp_id)
        for opp_id in expired:
            del self.sent_opportunities[opp_id]
        if expired:
            print(f"🗑️ Cleaned up {len(expired)} expired opportunities")
            self.save_sent_opportunities()
        return len(expired)
    def setup_handlers(self):
        """Configure command and callback handlers"""
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("subscribe", self.subscribe))
        self.app.add_handler(CommandHandler("unsubscribe", self.unsubscribe))
        self.app.add_handler(CommandHandler("status", self.status))
        self.app.add_handler(CommandHandler("admin", self.admin_panel))
        self.app.add_handler(CommandHandler("stats", self.admin_stats))
        self.app.add_handler(CommandHandler("broadcast", self.admin_broadcast))
        self.app.add_handler(CommandHandler("check", self.admin_check_now))
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome message"""
        user = update.effective_user
        welcome_text = f"""
🎯 <b>Welcome to Polymarket Signal Bot!</b>
Hello {user.first_name}! 👋
I'm your intelligent assistant for identifying profitable opportunities on Polymarket.
🔔 <b>What I do:</b>
• Analyze weather prediction markets in real-time
• Use accurate weather forecasts to find mispriced markets
• Send instant alerts to subscribers
• Provide direct links to opportunities
<b>⚠️ Important:</b>
Opportunities are <b>ONLY</b> sent to subscribed users!
<b>Available commands:</b>
/subscribe - Start receiving opportunity alerts
/unsubscribe - Stop receiving alerts
/status - Check your subscription status
/help - Help and information
Ready to start? Use /subscribe! 🚀
"""
        keyboard = [
            [InlineKeyboardButton("🔔 Subscribe Now", callback_data="subscribe")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command"""
        help_text = """
📚 <b>Help Center</b>
<b>Main Commands:</b>
/start - Start the bot
/subscribe - Activate notifications
/unsubscribe - Deactivate notifications
/status - Check your status
/help - This message
<b>How it works:</b>
1️⃣ The bot analyzes Polymarket weather prediction markets
2️⃣ Compares market prices with accurate weather forecasts
3️⃣ When a mispriced opportunity is found, <b>ONLY subscribers</b> receive alerts
4️⃣ Each alert contains the expected temperature and best markets to bet on
<b>Signal Types:</b>
🟢 <b>High Confidence</b> - Strong opportunity (forecast very accurate)
🟡 <b>Medium Confidence</b> - Good opportunity (forecast reliable)
🔵 <b>Low Confidence</b> - Interesting market (forecast less certain)
<b>⚠️ Remember:</b>
You must be subscribed to receive opportunities!
Questions? Contact support!
"""
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)
    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Subscribe user to receive alerts"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        if user_id in self.subscribers:
            await update.message.reply_text(
                "✅ You're already subscribed to receive alerts!",
                parse_mode=ParseMode.HTML
            )
        else:
            self.subscribers.add(user_id)
            self.save_subscribers()
            text = f"""
🎉 <b>Welcome Aboard, {user_name}!</b>
Your subscription is now <b>ACTIVE</b>! 🔔
<b>Active settings:</b>
✓ Weather market alerts
✓ Forecast-based analysis
✓ Direct links to markets
✓ Real-time notifications
You will now receive exclusive opportunities as they are detected!
Use /unsubscribe anytime to deactivate.
<i>Happy trading! 📈</i>
"""
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unsubscribe user"""
        user_id = update.effective_user.id
        if user_id in self.subscribers:
            self.subscribers.remove(user_id)
            self.save_subscribers()
            text = """
🔕 <b>Subscription Cancelled</b>
You will no longer receive opportunity alerts.
Use /subscribe anytime to reactivate and start receiving signals again.
We hope to see you back soon! 👋
"""
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(
                "❌ You're not subscribed. Use /subscribe to receive alerts.",
                parse_mode=ParseMode.HTML
            )
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user status"""
        user_id = update.effective_user.id
        is_subscribed = user_id in self.subscribers
        status_icon = "🟢" if is_subscribed else "🔴"
        status_text = "Active" if is_subscribed else "Inactive"
        text = f"""
📊 <b>Your Status</b>
{status_icon} <b>Alerts:</b> {status_text}
👤 <b>User ID:</b> <code>{user_id}</code>
📈 <b>Total subscribers:</b> {len(self.subscribers)}
🔄 <b>Bot Status:</b> {"Running" if self.is_running else "Idle"}
{"✅ You're receiving exclusive opportunities! 🎉" if is_subscribed else "❌ You're missing out on opportunities! Use /subscribe to activate."}
"""
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for inline buttons"""
        query = update.callback_query
        await query.answer()
        if query.data == "subscribe":
            user_id = query.from_user.id
            user_name = query.from_user.first_name
            if user_id not in self.subscribers:
                self.subscribers.add(user_id)
                self.save_subscribers()
                await query.edit_message_text(
                    f"🎉 <b>Subscribed Successfully!</b>\n\nWelcome {user_name}! You'll now receive exclusive opportunity alerts.",
                    parse_mode=ParseMode.HTML
                )
            else:
                await query.edit_message_text(
                    "✅ You're already subscribed!",
                    parse_mode=ParseMode.HTML
                )
        elif query.data == "help":
            help_text = """
📚 <b>Quick Help</b>
Use /subscribe to receive opportunity alerts.
Only subscribed users receive signals!
Use /help for detailed information.
"""
            await query.edit_message_text(help_text, parse_mode=ParseMode.HTML)
    def is_admin(self, user_id):
        """Check if user is admin"""
        return user_id in ADMIN_IDS
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin control panel"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized. Admin access only.")
            return
        text = """
👨‍💼 <b>ADMIN PANEL</b>
<b>Available Commands:</b>
/stats - View bot statistics
/broadcast <message> - Send message to all subscribers
/check - Manually check for opportunities now
/admin - Show this panel
<b>Current Status:</b>
📊 Total Subscribers: {subs}
🟢 Bot Status: {status}
🔄 Check Interval: {interval}s
Use these commands to manage the bot.
""".format(
    subs=len(self.subscribers),
    status="Running" if self.is_running else "Idle",
    interval=CHECK_INTERVAL
)
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    async def admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed statistics"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized. Admin access only.")
            return
        text = f"""
📊 <b>BOT STATISTICS</b>
<b>Users:</b>
• Total Subscribers: {len(self.subscribers)}
• Admin ID: <code>{user_id}</code>
<b>System:</b>
• Status: 🟢 Online
• Opportunities Sent: {len(self.sent_opportunities)}
• Last Check: {datetime.now().strftime("%m/%d/%Y %H:%M")}
<b>Subscriber IDs:</b>
{chr(10).join([f"• <code>{sub_id}</code>" for sub_id in list(self.subscribers)[:10]])}
{f"• ... and {len(self.subscribers) - 10} more" if len(self.subscribers) > 10 else ""}
"""
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    async def admin_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast message to all subscribers"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized. Admin access only.")
            return
        message_text = " ".join(context.args)
        if not message_text:
            await update.message.reply_text(
                "⚠️ Usage: /broadcast <your message>\n\nExample: /broadcast Important update for all users!"
            )
            return
        await update.message.reply_text("📤 Sending broadcast...")
        broadcast_msg = f"""
📢 <b>ADMIN ANNOUNCEMENT</b>
{message_text}
"""
        successful = 0
        failed = 0
        for sub_id in self.subscribers.copy():
            try:
                await self.app.bot.send_message(
                    chat_id=sub_id,
                    text=broadcast_msg,
                    parse_mode=ParseMode.HTML
                )
                successful += 1
                await asyncio.sleep(0.05)
            except Exception as e:
                print(f"Failed to send to {sub_id}: {e}")
                if "bot was blocked by the user" in str(e).lower():
                    self.subscribers.discard(sub_id)
                failed += 1
        await update.message.reply_text(
            f"✅ Broadcast complete!\n\n📊 Sent: {successful}\n❌ Failed: {failed}"
        )
    async def admin_check_now(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manually trigger opportunity check"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Unauthorized. Admin access only.")
            return
        await update.message.reply_text("🔍 Checking for opportunities now...")
        await self.check_opportunities()
        await update.message.reply_text("✅ Check complete!")
    async def check_opportunities(self):
        """Check for new opportunities using your analysis code"""
        try:
            cleaned = self.cleanup_old_opportunities()
            print(f"\n{'='*60}")
            print(f"🔍 Checking opportunities at {datetime.now()}")
            print(f"👥 Current subscribers: {len(self.subscribers)}")
            print(f"📝 Already sent opportunities: {len(self.sent_opportunities)}")
            if cleaned > 0:
                print(f"🗑️ Cleaned {cleaned} expired opportunities")
            print(f"{'='*60}\n")
            events = fetch_search()
            print(f"📊 Found {len(events)} events from Polymarket")
            for m in events:
                question = m["title"]
                unit = m["markets"][0]["groupItemTitle"]
                parsed = parse_question(question, unit)
                if not parsed:
                    print(f"⚠️ Could not parse: {question}")
                    continue
                if parsed["type"] != "temperature":
                    print(f"⏭️ Skipping non-temperature market: {question}")
                    continue
                opportunity_id = m["slug"]
                if opportunity_id in self.sent_opportunities:
                    print(f"⏭️ Already sent: {opportunity_id}")
                    continue
                print(f"\n{'─'*60}")
                print(f"📊 Analyzing: {question}")
                print(f"🔗 URL: polymarket.com/event/{m['slug']}")
                print(f"📋 Parsed data: {parsed}")
                weather = fetch_weather(parsed["lat"], parsed["lon"], m["endDate"], parsed["unit"])
                print(f"🌤️ Weather forecast: {weather}")
                best, second_best = best_market(m["markets"], weather["temperature_max"])
                if not best or not second_best:
                    print(f"❌ Could not find best markets")
                    continue
                print(f"🎯 Best market: {best[1]['slug']}")
                print(f"🥈 Second best: {second_best[1]['slug']}")
                opportunity_data = {
                    "title": question,
                    "forecast_temp": f"{weather['temperature_max']:.1f}°{parsed['unit'][0].upper()}",
                    "best_market": best[1]['groupItemTitle'],
                    "link": f"https://polymarket.com/event/{m['slug']}",
                    "analysis": self.generate_analysis(weather, best, second_best, parsed),
                    "date": m["endDate"].split("T")[0],
                    "city": parsed["city"]
                }
                print(f"📤 Sending signal to {len(self.subscribers)} subscribers...")
                await self.send_signal(opportunity_data)
                self.sent_opportunities[opportunity_id] = datetime.now().timestamp()
                self.save_sent_opportunities()
                print(f"✅ Signal sent and marked as sent (expires in {OPPORTUNITY_EXPIRY//60} minutes)")
                print(f"{'─'*60}\n")
                await asyncio.sleep(2)
        except Exception as e:
            print(f"❌ Error checking opportunities: {e}")
            import traceback
            traceback.print_exc()
    def generate_analysis(self, weather, best, second_best, parsed):
        """Generate analysis text"""
        temp = weather['temperature_max']
        best_range = best[1]['groupItemTitle']
        second_range = second_best[1]['groupItemTitle']
        analysis = f"""
<b>Weather Forecast:</b> {temp:.1f}°{parsed['unit'][0].upper()}
<b>Best Market:</b> {best_range}
This range contains the forecasted temperature, making it the most likely outcome.
<b>Backup Option:</b> {second_range}
Second most likely if forecast shifts slightly.
<b>Risk Assessment:</b>
Weather forecasts for {parsed['city']} are generally reliable for this timeframe. The market appears mispriced compared to meteorological data.
"""
        return analysis.strip()
    async def send_signal(self, opportunity_data):
        """Send opportunity signal to all subscribers ONLY"""
        print(f"\n📨 send_signal called")
        print(f"👥 Subscribers list: {self.subscribers}")
        print(f"📊 Number of subscribers: {len(self.subscribers)}")
        if not self.subscribers:
            print("⚠️ No subscribers to send signal to.")
            return
        print(f"✅ Preparing to send to {len(self.subscribers)} subscribers")
        message = f"""
🎯 <b>NEW OPPORTUNITY - Weather Market</b>
<b>🌡️ Market:</b> {opportunity_data['title']}
<b>📍 Location:</b> {opportunity_data['city']}
<b>📅 Date:</b> {opportunity_data['date']}
<b>💰 Data:</b>
• Forecasted Temperature: {opportunity_data['forecast_temp']}
• Best Market: {opportunity_data['best_market']}
<b>📊 Analysis:</b>
{opportunity_data['analysis']}
<b>⏰ Sent at:</b> {datetime.now().strftime("%m/%d/%Y %H:%M UTC")}
<i>💡 Exclusive signal for subscribers only</i>
"""
        keyboard = [
            [InlineKeyboardButton("🔗 Open Market", url=opportunity_data['link'])],
            [InlineKeyboardButton("📈 Trade Now", url=opportunity_data['link'])]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        successful = 0
        failed = 0
        print(f"🔄 Starting to send to subscribers...")
        for user_id in self.subscribers.copy():
            try:
                print(f"  → Sending to user {user_id}...")
                await self.app.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
                successful += 1
                print(f"  ✅ Successfully sent to {user_id}")
                await asyncio.sleep(0.05)
            except Exception as e:
                print(f"  ❌ Error sending to {user_id}: {e}")
                if "bot was blocked by the user" in str(e).lower():
                    self.subscribers.discard(user_id)
                    self.save_subscribers()
                    print(f"  🚫 Removed {user_id} from subscribers (blocked bot)")
                failed += 1
        print(f"\n📊 SEND SUMMARY:")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"👥 Remaining subscribers: {len(self.subscribers)}\n")
    async def background_check(self):
        """Background task to periodically check for opportunities"""
        self.is_running = True
        print(f"🔄 Background checker started (interval: {CHECK_INTERVAL}s)")
        while self.is_running:
            try:
                await self.check_opportunities()
                await asyncio.sleep(CHECK_INTERVAL)
            except Exception as e:
                print(f"❌ Error in background check: {e}")
                await asyncio.sleep(60)
    async def post_init(self, application):
        """Called after the bot starts"""
        asyncio.create_task(self.background_check())
    def run(self):
        """Start the bot"""
        print("🤖 Bot started and running...")
        print(f"📊 {len(self.subscribers)} active subscribers")
        self.app.post_init = self.post_init
        self.app.run_polling()
if __name__ == '__main__':
    bot = PolymarketBot(TOKEN)
    bot.run()
