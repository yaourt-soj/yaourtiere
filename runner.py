import bot

while True:
    try:
        bot.Yaourtiere().run_bot()
    except Exception as e:
        print("Bot crashed:", e)
        print("Restarting bot")