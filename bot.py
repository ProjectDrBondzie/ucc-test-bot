import os
import pandas as pd
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ============================================
# GET TOKEN FROM RAILWAY ENVIRONMENT VARIABLE
# ============================================
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8665911975:AAHtyG2P-ECob4hQCIdKN0as9054lgrMm0I")

# ============================================
# CREATE CSV FILE IF IT DOESN'T EXIST
# ============================================
CSV_COLUMNS = [
    "user_id", "username", "group", "submission_time",
    "age", "gender", "year_of_study", "programme",
    "email_usage", "mobile_money_usage", "social_media_usage",
    "knows_phishing", "phishing_definition", "identifies_indicators",
    "received_suspicious", "prior_compromise", "prior_training",
    "scenario_1", "scenario_2", "scenario_3", "scenario_4", "scenario_5",
    "uses_2fa", "shares_password", "report_suspicious", "score"
]

if not os.path.exists("data.csv"):
    df = pd.DataFrame(columns=CSV_COLUMNS)
    df.to_csv("data.csv", index=False)
    print("✅ data.csv created successfully")

# ============================================
# STORE USER SESSIONS (TEMPORARY DATA)
# ============================================
user_sessions = {}

# ============================================
# START COMMAND - FIRST QUESTION
# ============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = {"step": "group", "answers": {}}
    
    keyboard = [
        [InlineKeyboardButton("📊 STEM", callback_data="STEM")],
        [InlineKeyboardButton("📚 NON-STEM", callback_data="NON-STEM")]
    ]
    
    await update.message.reply_text(
        "🎓 WELCOME TO THE UCC CYBER SECURITY STUDY 🎓\n\n"
        "This research compares phishing awareness between STEM and NON-STEM students.\n\n"
        "✅ All responses are anonymous\n"
        "✅ Takes 3-4 minutes\n"
        "✅ Your data helps improve cybersecurity education\n\n"
        "Please select your academic group:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============================================
# STATS COMMAND - CHECK RESPONSES (RESEARCHER ONLY)
# ============================================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = pd.read_csv("data.csv")
    
    if len(df) == 0:
        await update.message.reply_text("📊 No responses collected yet. Share the bot with students!")
        return
    
    stem = len(df[df['group'] == 'STEM'])
    nonstem = len(df[df['group'] == 'NON-STEM'])
    total = len(df)
    
    # Calculate average susceptibility score (0-5, higher = more vulnerable)
    avg_score = df['score'].mean() if 'score' in df.columns else 0
    
    await update.message.reply_text(
        f"📊 STUDY PROGRESS REPORT 📊\n\n"
        f"📝 Total responses: {total}\n"
        f"🔬 STEM students: {stem}\n"
        f"📖 NON-STEM students: {nonstem}\n"
        f"⚠️ Average vulnerability score: {avg_score:.1f}/5\n\n"
        f"Higher score = more susceptible to phishing"
    )

# ============================================
# HANDLE GROUP SELECTION
# ============================================
async def group_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_sessions[user_id]["answers"]["group"] = query.data
    user_sessions[user_id]["step"] = "age"
    
    keyboard = [
        [InlineKeyboardButton("18-21", callback_data="18-21")],
        [InlineKeyboardButton("22-25", callback_data="22-25")],
        [InlineKeyboardButton("26-30", callback_data="26-30")],
        [InlineKeyboardButton("31+", callback_data="31+")]
    ]
    
    await query.edit_message_text(
        "📋 QUESTION 1/19\n\nWhat is your age range?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============================================
# MASTER QUESTION HANDLER
# ============================================
async def question_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    current_step = user_sessions[user_id]["step"]
    user_sessions[user_id]["answers"][current_step] = query.data
    
    # Define the question flow (step -> next_step, question_text, options)
    flow = {
        "age": ("gender", "📋 QUESTION 2/19\n\nWhat is your gender?",
                [("👨 Male", "male"), ("👩 Female", "female"), ("🔒 Prefer not to say", "prefer_not")]),
        
        "gender": ("year", "📋 QUESTION 3/19\n\nWhat is your year of study?",
                   [("Level 100", "100"), ("Level 200", "200"), ("Level 300", "300"), ("Level 400", "400")]),
        
        "year": ("programme", "📋 QUESTION 4/19\n\nSelect your programme type:",
                 [("🔬 Sciences", "sciences"), ("📖 Humanities", "humanities"), 
                  ("💼 Business", "business"), ("📚 Education", "education"), ("⚖️ Law", "law")]),
        
        "programme": ("email", "📋 QUESTION 5/19\n\nHow often do you use email?",
                      [("📧 Daily", "daily"), ("📧 Several times/week", "weekly"), 
                       ("📧 Occasionally", "occasional"), ("📧 Rarely", "rarely")]),
        
        "email": ("mobile_money", "📋 QUESTION 6/19\n\nHow often do you use mobile money or online banking?",
                  [("💰 Very often", "very_often"), ("💰 Often", "often"), 
                   ("💰 Sometimes", "sometimes"), ("💰 Never", "never")]),
        
        "mobile_money": ("social_media", "📋 QUESTION 7/19\n\nHow often do you use social media?",
                         [("📱 Daily", "daily"), ("📱 Several times/week", "weekly"), 
                          ("📱 Occasionally", "occasional"), ("📱 Rarely", "rarely")]),
        
        "social_media": ("knows_phishing", "📋 QUESTION 8/19\n\nAre you familiar with the term 'phishing'?",
                         [("✅ Yes", "yes"), ("❌ No", "no"), ("🤔 Not sure", "not_sure")]),
        
        "knows_phishing": ("definition", "📋 QUESTION 9/19\n\nWhat does phishing primarily refer to?",
                           [("🎣 Tricking users to reveal info", "correct"), 
                            ("🛡️ Antivirus software", "wrong"), 
                            ("🔐 Secure login method", "wrong")]),
        
        "definition": ("indicators", "📋 QUESTION 10/19\n\nWhich is a common indicator of phishing?",
                       [("⚠️ Urgent language", "urgent"), ("✨ Professional design", "wrong"),
                        ("🏢 Official logo", "wrong"), ("🤷 Not sure", "not_sure")]),
        
        "indicators": ("received", "📋 QUESTION 11/19\n\nHave you ever received a suspicious message asking for personal info?",
                       [("⚠️ Yes, frequently", "frequently"), ("⚠️ Yes, occasionally", "occasionally"),
                        ("✅ No", "no"), ("🤔 Not sure", "not_sure")]),
        
        "received": ("compromise", "📋 QUESTION 12/19\n\nHave you ever had an account compromised or lost money online?",
                     [("⚠️ Yes", "yes"), ("✅ No", "no"), ("🔒 Prefer not to say", "prefer_not")]),
        
        "compromise": ("training", "📋 QUESTION 13/19\n\nHave you received any formal cybersecurity training?",
                       [("✅ Yes", "yes"), ("❌ No", "no"), ("🤔 Not sure", "not_sure")]),
        
        "training": ("scenario1", "📧 SCENARIO 1/5\n\nEmail from 'UCC IT Helpdesk': 'Your password expires today. Click here to keep it.'\n\nWhat do you do?",
                     [("❌ Click the link", "clicked"), ("✅ Check with IT department first", "safe"), ("🗑️ Delete email", "safe")]),
        
        "scenario1": ("scenario2", "📱 SCENARIO 2/5\n\nSMS: 'Your MTN mobile money has been credited GHS 500. Claim now: http://short.link'\n\nWhat do you do?",
                      [("❌ Click link", "clicked"), ("✅ Ignore and delete", "safe"), ("✅ Call MTN official line", "safe")]),
        
        "scenario2": ("scenario3", "💼 SCENARIO 3/5\n\nLinkedIn message: 'Urgent job offer. Submit your login details to apply.'\n\nWhat do you do?",
                      [("❌ Submit details", "clicked"), ("✅ Ignore", "safe"), ("✅ Verify recruiter independently", "safe")]),
        
        "scenario3": ("scenario4", "🏦 SCENARIO 4/5\n\nBank email: 'Suspicious activity detected. Confirm your account now or it will be frozen.'\n\nWhat do you do?",
                      [("❌ Click confirmation link", "clicked"), ("✅ Call bank official number", "safe"), ("🗑️ Delete email", "safe")]),
        
        "scenario4": ("scenario5", "📧 SCENARIO 5/5\n\nEmail from a lecturer: 'Click here to download important course materials.' (The email has poor grammar)\n\nWhat do you do?",
                      [("❌ Click link", "clicked"), ("✅ Verify with lecturer directly", "safe"), ("🗑️ Ignore", "safe")]),
        
        "scenario5": ("2fa", "📋 QUESTION 18/19\n\nDo you use two-factor authentication (2FA) where available?",
                      [("✅ Always", "always"), ("⚠️ Sometimes", "sometimes"), ("❌ Never", "never"), ("🤷 Don't know what it is", "dont_know")]),
        
        "2fa": ("share_password", "📋 QUESTION 19/19\n\nHave you ever shared your password with anyone?",
                [("✅ Yes", "yes"), ("❌ No", "no"), ("⚠️ Only close friends/family", "sometimes")]),
    }
    
    if current_step in flow:
        next_step, question_text, options = flow[current_step]
        user_sessions[user_id]["step"] = next_step
        keyboard = [[InlineKeyboardButton(label, callback_data=value)] for label, value in options]
        await query.edit_message_text(question_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    else:
        # END OF SURVEY - SAVE TO CSV
        answers = user_sessions[user_id]["answers"]
        answers["share_password"] = query.data  # Last question answer
        answers["submission_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate vulnerability score (0-5, higher = more vulnerable)
        score = 0
        for i in range(1, 6):
            if answers.get(f"scenario{i}", "") == "clicked":
                score += 1
        
        # Prepare row for CSV
        row = {
            "user_id": query.from_user.id,
            "username": query.from_user.username,
            "group": answers.get("group", ""),
            "submission_time": answers.get("submission_time", ""),
            "age": answers.get("age", ""),
            "gender": answers.get("gender", ""),
            "year_of_study": answers.get("year", ""),
            "programme": answers.get("programme", ""),
            "email_usage": answers.get("email", ""),
            "mobile_money_usage": answers.get("mobile_money", ""),
            "social_media_usage": answers.get("social_media", ""),
            "knows_phishing": answers.get("knows_phishing", ""),
            "phishing_definition": answers.get("definition", ""),
            "identifies_indicators": answers.get("indicators", ""),
            "received_suspicious": answers.get("received", ""),
            "prior_compromise": answers.get("compromise", ""),
            "prior_training": answers.get("training", ""),
            "scenario_1": answers.get("scenario1", ""),
            "scenario_2": answers.get("scenario2", ""),
            "scenario_3": answers.get("scenario3", ""),
            "scenario_4": answers.get("scenario4", ""),
            "scenario_5": answers.get("scenario5", ""),
            "uses_2fa": answers.get("2fa", ""),
            "shares_password": answers.get("share_password", ""),
            "report_suspicious": "",
            "score": score,
        }
        
        # Save to CSV
        df = pd.read_csv("data.csv")
        df.loc[len(df)] = row
        df.to_csv("data.csv", index=False)
        
        # Thank you message
        await query.edit_message_text(
            "✅ THANK YOU FOR COMPLETING THE STUDY! ✅\n\n"
            "Your responses have been recorded anonymously.\n\n"
            f"📊 Your phishing vulnerability score: {score}/5\n"
            f"{'⚠️ Higher scores indicate more susceptibility to phishing attacks' if score >= 3 else '✅ Lower scores indicate good phishing awareness'}\n\n"
            "🔒 This research will help improve cybersecurity education at UCC.\n\n"
            "You may now close this chat."
        )
        
        # Clean up session
        del user_sessions[user_id]

# ============================================
# MAIN FUNCTION
# ============================================
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(group_handler, pattern="^(STEM|NON-STEM)$"))
    app.add_handler(CallbackQueryHandler(question_handler))
    
    print("🤖 UCC Phishing Study Bot is running...")
    print("📊 Data will be saved to data.csv automatically")
    app.run_polling()

if __name__ == "__main__":
    main()