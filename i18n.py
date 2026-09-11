MESSAGES = {
    "zh-CN": {
        "welcome": "🎯 欢迎使用 CheckPause！",
        "welcome_back": "🎯 欢迎回来，{username}！",
        "first_setup": "首次使用，请输入你的用户名",
        "username": "用户名：",
        "profile_created": "✅ 用户档案创建成功！欢迎你，{username}！\n",
        "choose_language": "请选择 CLI 语言 / Select CLI language:\n1. 中文\n2. English",
        "language_choice": "请输入选项 / Enter choice: ",
        "invalid_language": "无效选项，默认使用中文。",
        "language_changed": "✅ CLI 语言已切换为中文。",
        "paste_pgn": "请粘贴你的 PGN 棋谱，然后在新的一行输入 END：",
        "confirm_delete": "⚠️ 确认删除所有用户数据吗？此操作无法撤销！（y/n）：",
        "data_cleared": "✅ 所有用户数据已清除，请重新启动程序。",
        "profile_not_found": "⚠️ 未找到用户档案文件。",
        "deletion_cancelled": "✅ 已取消删除。",
        "thinking": "💭 思考中... ({seconds:.1f}s)",
        "goodbye": "👋 再见！",
        "parsing": "📥 正在解析 PGN...",
        "success": " 成功",
        "failed": " 失败",
        "parse_error": "❌ PGN 解析错误：{error}",
        "engine_analyzing": "⚙️ Stockfish 引擎分析中...",
        "ready": "\n✅ 分析完成",
        "error": "❌ 错误：{error}",
        "username_stat": "🎯 用户名：{username}",
        "analysis_date": "📅 分析日期：{date}",
        "latest_accuracy": "📈 本局准确度：{accuracy}%",
        "average_accuracy": "📊 平均准确度：{accuracy:.1f}%{trend}",
        "total_games": "📊 对局总数：{total}",
        "stats": "\n📊 你的数据：",
        "last_game": "   ─ 最近对局：{date}",
        "average_stat": "   ─ 平均准确度：{accuracy:.1f}%",
        "total_stat": "   ─ 对局总数：{total}",
    },
    "en-US": {
        "welcome": "🎯 Welcome to CheckPause!",
        "welcome_back": "🎯 Welcome back, {username}!",
        "first_setup": "First-time setup. Please enter your username",
        "username": "Username: ",
        "profile_created": "✅ Profile created! Welcome, {username}!\n",
        "choose_language": "请选择 CLI 语言 / Select CLI language:\n1. 中文\n2. English",
        "language_choice": "请输入选项 / Enter choice: ",
        "invalid_language": "Invalid choice. Chinese will be used by default.",
        "language_changed": "✅ CLI language changed to English.",
        "paste_pgn": "Please paste your PGN game, then enter END on a new line:",
        "confirm_delete": "⚠️ Confirm delete all user data? This cannot be undone! (y/n): ",
        "data_cleared": "✅ All user data cleared. Please restart the program.",
        "profile_not_found": "⚠️ Profile file not found.",
        "deletion_cancelled": "✅ Deletion cancelled.",
        "thinking": "💭 Thinking... ({seconds:.1f}s)",
        "goodbye": "👋 Goodbye~",
        "parsing": "📥 Parsing PGN...",
        "success": " Success",
        "failed": " Failed",
        "parse_error": "❌ PGN parse error: {error}",
        "engine_analyzing": "⚙️ Stockfish engine analyzing...",
        "ready": "\n✅ Ready",
        "error": "❌ Error: {error}",
        "username_stat": "🎯 Username: {username}",
        "analysis_date": "📅 Analysis date: {date}",
        "latest_accuracy": "📈 Latest accuracy: {accuracy}%",
        "average_accuracy": "📊 Average accuracy: {accuracy:.1f}%{trend}",
        "total_games": "📊 Total games: {total}",
        "stats": "\n📊 Your stats:",
        "last_game": "   ─ Last game: {date}",
        "average_stat": "   ─ Average accuracy: {accuracy:.1f}%",
        "total_stat": "   ─ Total games: {total}",
    },
}


def t(key, language="zh-CN", **values):
    return MESSAGES.get(language, MESSAGES["zh-CN"])[key].format(**values)


def choose_language():
    print(MESSAGES["zh-CN"]["choose_language"])
    choice = input(MESSAGES["zh-CN"]["language_choice"]).strip()
    if choice == "2":
        return "en-US"
    if choice != "1":
        print(MESSAGES["zh-CN"]["invalid_language"])
    return "zh-CN"
