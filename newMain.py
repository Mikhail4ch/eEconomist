import telebot
from telebot import types
from TOP import TOP5
from Bitz import BITZ

bot = telebot.TeleBot('7968913931:AAFrFTAOgxaiN4MoMOPhHJmk3o5qAnsgYNc')

# Tracking
USER_MSG_IDS = {}         # For context (yields, etc.)
PERMANENT_MSG_IDS = {}    # For all "permanent" UI messages
MENU_IMAGE_ID = {}        # Last sent menu image (book.png) per user
EARNING_STATE = set()

# NEW: For sticky/menu messages sent from sticky button!
STICKY_MSG_ID = {}
LAST_MENU_MSG_ID = {}

ASSETS = {
    '$BITZ ⛏️': 'BITZ',
    '$tUSD 💵': 'TUSD',
    '$tETH 💎': 'tETH',
    '$ETH 💎': 'ETH',
    '$USDC 💵': 'USDC',
    '$USDT 💵': 'USDT',
    '$SOL 🚀': 'SOL',
    '$LAIKA 🐶': 'LAIKA'
}

def sticky_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Table of contents 🔙'))
    return markup

def track_user_msg(user_id, msg_id):
    USER_MSG_IDS.setdefault(user_id, []).append(msg_id)

def delete_user_msgs(chat_id, user_id):
    permanent = set(PERMANENT_MSG_IDS.get(user_id, []))
    for msg_id in USER_MSG_IDS.get(user_id, []):
        if msg_id not in permanent:
            try:
                bot.delete_message(chat_id, msg_id)
            except Exception:
                pass
    USER_MSG_IDS[user_id] = []

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    EARNING_STATE.discard(user_id)

    # Welcome image and greeting
    file = open('./Eclipse Economy.jpeg', 'rb')
    photo_msg = bot.send_photo(chat_id, file)
    welcome_msg = bot.send_message(
        chat_id,
        "GSVM Eclipsooor 💚\nWelcome to the valley of Eclipse economy opportunities 🌄"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('eEconomist guidebook 📗', callback_data='main_menu'))
    button_msg = bot.send_message(
        chat_id,
        'Grab your 👇',
        reply_markup=markup
    )
    # Track as permanent
    PERMANENT_MSG_IDS[user_id] = [photo_msg.message_id, welcome_msg.message_id, button_msg.message_id]
    USER_MSG_IDS[user_id] = [button_msg.message_id]

    # Clean sticky/menu trackers
    STICKY_MSG_ID[user_id] = None
    LAST_MENU_MSG_ID[user_id] = None
    MENU_IMAGE_ID[user_id] = None

@bot.callback_query_handler(func=lambda call: call.data == 'main_menu')
def menu_entry_point(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    # Clean up previous sticky/menu (from sticky button)
    if STICKY_MSG_ID.get(user_id):
        try: bot.delete_message(chat_id, STICKY_MSG_ID[user_id])
        except: pass
    if LAST_MENU_MSG_ID.get(user_id):
        try: bot.delete_message(chat_id, LAST_MENU_MSG_ID[user_id])
        except: pass
    STICKY_MSG_ID[user_id] = None
    LAST_MENU_MSG_ID[user_id] = None

    # 1. Send menu image (book.png)
    file = open('./book.png', 'rb')
    photo_msg = bot.send_photo(chat_id, file)
    MENU_IMAGE_ID[user_id] = photo_msg.message_id
    PERMANENT_MSG_IDS.setdefault(user_id, []).append(photo_msg.message_id)

    # 2. Send menu message with keyboard
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Highest Yield 🏆 in the last 24H 🕔 (🔐)', callback_data='yield'))
    markup.add(types.InlineKeyboardButton('$BITZ stacking performance 🥩 (🔐)', callback_data='bitz'))
    markup.add(types.InlineKeyboardButton('Retroactive points 🪂 (🔐)', callback_data='points'))
    markup.add(types.InlineKeyboardButton('Cross-chain opportunities 🤞⛓️ (🔐)', callback_data='crosschain'))
    markup.add(types.InlineKeyboardButton('GameFi 🎮 & 💰(🔒)', callback_data='other_chapters'))
    menu_msg = bot.send_message(
        chat_id,
        '<b>Table of contents</b> 📜',
        parse_mode='HTML',
        reply_markup=markup
    )
    PERMANENT_MSG_IDS[user_id].append(menu_msg.message_id)

    # 3. Sticky button below menu for convenience
    sticky_msg = bot.send_message(
        chat_id,
        "To return to the Table of contents anytime use the Menu or press the button below 👇",
        reply_markup=sticky_menu_keyboard()
    )
    PERMANENT_MSG_IDS[user_id].append(sticky_msg.message_id)

    # Remove the "grab your" button
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except Exception:
        pass

@bot.message_handler(func=lambda m: m.text == 'Table of contents 🔙')
def menu_from_sticky(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # 1. Clean up: delete all context messages
    delete_user_msgs(chat_id, user_id)

    # 2. Optionally delete the sticky button message itself (if you want)
    try:
        bot.delete_message(chat_id, message.message_id)
    except Exception:
        pass

# ---- Menu Handlers for yield/other_chapters ----

@bot.callback_query_handler(func=lambda call: call.data in ['yield', 'points', 'crosschain','other_chapters','bitz'])
def handle_menu(call):
    if call.data == 'yield':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('eEconomy pillars 🏛: $BITZ, $tETH, $tUSD and $ES', callback_data='pillars'))
        markup.add(types.InlineKeyboardButton('Other assets 📊: $ETH, $USDC, $SOL and etc.', callback_data='other_assets'))
        msg = bot.send_message(call.message.chat.id, "Choose pool group fam 🤔", reply_markup=markup)
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'points':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Invariant 🔱', callback_data='invariant'))
        markup.add(types.InlineKeyboardButton('Umbra 🃏', callback_data='umbra'))
        markup.add(types.InlineKeyboardButton('Astrol 🔷', callback_data='astrol'))
        markup.add(types.InlineKeyboardButton('AllDomains 🧘‍♂️', callback_data='alldomains'))
        markup.add(types.InlineKeyboardButton('EnsoFi ❇️', callback_data='ensofi'))
        msg = bot.send_message(call.message.chat.id, "Choose DApp to earn retroactive points, fam 🎯\n\nNever underestimate ecosystem drops especially on Eclipse 🙃", reply_markup=markup)
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'crosschain':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Hyperlane ⏩', callback_data='hyperlane'))
        markup.add(types.InlineKeyboardButton('Relay 🕺', callback_data='relay'))
        markup.add(types.InlineKeyboardButton('More to come 🔜',callback_data='disabled'))
        msg = bot.send_message(call.message.chat.id,"<b>Retroactive</b> cross-chain interactions like 🌉 between Eclipse and other block⛓️s", parse_mode='html', reply_markup=markup)
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'bitz':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Data about staking APR％', callback_data='stacking'))
        markup.add(types.InlineKeyboardButton('Check how much you will earn 🫰', callback_data='earning'))
        msg = bot.send_message(call.message.chat.id,"Let's look at incredible <b>$BITZ</b> upside 🔋", parse_mode='html', reply_markup=markup)
        track_user_msg(call.from_user.id, msg.message_id)
    else:
        msg = bot.send_message(call.message.chat.id, "Coming tho0on!")
        track_user_msg(call.from_user.id, msg.message_id)
    
@bot.callback_query_handler(func=lambda call: call.data == 'disabled')
def disabled_callback(call):
    bot.answer_callback_query(call.id, "Coming soon 🚧", show_alert=False)

@bot.callback_query_handler(func=lambda call: call.data in ['stacking', 'earning'])
def handle_bitz(call):
    if call.data == 'stacking':
        bitz = BITZ()
        dataBout24H = bitz.findOutApr()
        dataAnnual = bitz.annualAPR()
        msg = bot.send_message(
            call.message.chat.id,
            f'Current $BITZ 24H APR:\n\n✅{dataBout24H}\nCurrent $BITZ annual APR:\n✅{dataAnnual}',
            parse_mode='html',
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'earning':
        EARNING_STATE.add(call.from_user.id)
        msg = bot.send_message(call.message.chat.id, 'Enter the number of $BITZ you want to stake, fam: ')
        track_user_msg(call.from_user.id, msg.message_id)

@bot.message_handler(func=lambda m: m.from_user.id in EARNING_STATE)
def get_potentialEarnings(message):
    user_id = message.from_user.id
    # NEW: Track the user's own message ID so it gets cleaned up!
    track_user_msg(user_id, message.message_id)
    try:
        staked = float(message.text.strip())
        if staked < 0:
            raise ValueError
    except Exception:
        msg = bot.send_message(message.chat.id, "❌ Enter a valid positive number for $BITZ amount.")
        track_user_msg(user_id, msg.message_id)
        return
    bitz = BITZ()
    forDay = bitz.howMuchEarnDaily(staked)
    forWeek = bitz.howMuchEarnWeekly(staked)
    forMonth = bitz.howMuchEarnMonthly(staked)
    forYear = bitz.howMuchYearly(staked)
    msg = bot.send_message(
        message.chat.id,
        f'Lets see fam how much $BITZ you will earn 👀\n\n💹{forDay}\n💹{forWeek}\n💹{forMonth}\n💹{forYear}')
    track_user_msg(user_id, msg.message_id)
    # Remove user from earning state
    EARNING_STATE.discard(user_id)

@bot.callback_query_handler(func=lambda call: call.data in ['pillars', 'other_assets'])
def handle_asset_group(call):
    if call.data == 'pillars':
        markup = types.InlineKeyboardMarkup()
        for key in ['$BITZ ⛏️', '$tUSD 💵', '$tETH 💎']:
            markup.add(types.InlineKeyboardButton(key, callback_data=key))
        markup.add(types.InlineKeyboardButton('$ES 🎇 (tho0on)', callback_data='disabled'))
        msg = bot.send_message(
            call.message.chat.id,
            "Choose one asset you want to earn with as a smart eEconomist 😉",
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'other_assets':
        markup = types.InlineKeyboardMarkup()
        for key in ['$ETH 💎', '$USDC 💵', '$USDT 💵', '$SOL 🚀', '$LAIKA 🐶']:
            markup.add(types.InlineKeyboardButton(key, callback_data=key))
        msg = bot.send_message(
            call.message.chat.id,
            "Choose one asset you want to earn with as a smart eEconomist 😉",
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data in ['hyperlane', 'relay'])
def handle_bridges_group(call):
    if call.data == 'hyperlane':
        markup = types.InlineKeyboardMarkup()
        url = 'https://www.usenexus.org/?origin=eclipsemainnet&destination=solanamainnet'
        markup.add(types.InlineKeyboardButton("Lets do some hyper-fast 🌉ing", url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "Although Hyperlane has already held its TGE, they’ll be distributing $HYPER rewards quarterly 😉\n\nTo be eligible you need to <b>spend $3 in Hyperlane fees</b> and the nearest snaphot will be on <b>30th of June ⛱</b>\n\nRoute instance: Solana 🔁 Eclipse (USDC & SOL)",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'relay':
        markup = types.InlineKeyboardMarkup()
        url = 'https://relay.link/bridge/eclipse?fromChainId=42161'
        markup.add(types.InlineKeyboardButton("Relay on Relay and do some 🌉ing", url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "Relay is currently the most prominent solution for bridging ETH between <b>other L2s and Eclipse</b> 🔥\n\nAs a rule bridges used to have their <b>own token</b> + Relay raised 14M$ not long ago ➡️ imo probability of <em>airdrop for bridging</em> is high but always <b>DYOR</b> \n\nRoute instance: Arbitrum 🔁 Eclipse (ETH)",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data in ['invariant', 'umbra', 'astrol', 'alldomains', 'ensofi'])
def handle_DApps_group(call):
    if call.data == 'invariant':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Pools with points 🔱', callback_data='poolswithpointsInvariant'))
        msg = bot.send_message(
            call.message.chat.id,
            "<em>Provide liquidity</em> to the pools and earn <strong>Invariant Points</strong> ✅\n\nRank at the top of the leaderboard to unlock <strong>points</strong> in other ecosystem projects too <em>(EDAS, EnsoFi and AllDomains)</em> 🎇",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'umbra':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Pools with points 🃏', callback_data='poolswithpointsUmbra'))
        msg = bot.send_message(
            call.message.chat.id,
            "<em>Add liquidity</em> to earn <strong>Umbra Points</strong> instead of fees + earn extra points based on <em>swap volume</em> 🧪\n\nNote: Epoch 7 has ended, so point distribution is <b>currently paused</b>. However, you can still complete retroactive activities, as they <b>may be rewarded</b> in the future ⛏️",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'astrol':
        url = 'https://app.astrol.io/'
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Check out the Astrol 🔷', url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "Astrol Protocol is a blue-chip lending platform where you can <em>lend and borrow</em> assets to earn <strong>Astrol Points</strong> for your needs at the same time earning Astrol Points 🎦\n\nEarn <strong>24 points</strong> per day for every $1 lent, <strong>72 points</strong> per day for every $1 borrowed and earn <strong>points</strong> by inviting your friends🚀",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'alldomains':
        url = 'https://eclipse.alldomains.id/profile/KwaPXHJ3bPjK34XTqUcjxkQDbCDMATeUijdqK6uHxYZ'
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('AllDomains eHome 🧘‍♂️', url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "AllDomains is the Web3 identity asset layer where you can <em>mint your unique domain</em> on Eclipse and earn <strong>points</strong> for it 😇\n\nThere are also plenty of other ways (simple and not) to earn <strong>AllDomains points</strong> - just explore them on their website 💻",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'ensofi':
        url1 = 'https://app.ensofi.xyz/?chain=ECLIPSE'
        url2 = 'https://e-lander.xyz/'
        url3 = 'https://www.edas.ensofi.xyz/Colossal'
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('EnsoFi lending hub on Eclipse 🌑 ', url=url1))
        markup.add(types.InlineKeyboardButton("E-Lander's NFT collection eHome 🏘", url=url2))
        markup.add(types.InlineKeyboardButton("'Colossal' DeFai ai-agent on Eclipse by E.D.A.S 👤", url=url3))
        msg = bot.send_message(
            call.message.chat.id,
            "EnsoFi is the cross-chain lending protocol which supports Eclipse/Solana/Sui\n\n1) Earn <strong>EnsoFi points</strong> by <em>lending & borrowing</em> assets, doing <em>daily check-in</em> and inviting friends 🤝\n2) Earn EnsoFi points by <em>holding and stacking</em> E-Lander NFTs 👨‍🎨\n3) Earn E.D.A.S points and $ profits by using their <em>DeFai ai-agent</em> 🤖",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data in ['poolswithpointsInvariant', 'poolswithpointsUmbra'])
def handle_poolswithpoints(call):
    if call.data == 'poolswithpointsInvariant':
        top = TOP5('')
        poolsDict = top.topPointsPools('Invariant')
        poolsActivity = top.topPointsPoolsActivity('Invariant')
        tvlData = top.topPointsPooolsTVL('Invariant')
        if not poolsDict:
            bot.send_message(call.message.chat.id, "No Invariant Points pools found at the moment.")
            return
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"]
        for idx, (pair_and_yield, url) in enumerate(poolsDict.items()):
            activity = poolsActivity.get(pair_and_yield, "N/A")
            tvl = tvlData.get(pair_and_yield, "N/A")
            medal = medals[idx] if idx < len(medals) else ""
            try:
                a = float(activity)
                if a > 0.2:
                    activity_str = 'High ✅'
                elif a > 0.05:
                    activity_str = 'Moderate ⚠️'
                else:
                    activity_str = 'Low ‼️'
            except:
                activity_str = str(activity)
            text = f"{medal} {pair_and_yield}\nPool activity: {activity_str}\nTvl: 💲{tvl}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🌐 Go to the pool", url=url))
            msg = bot.send_message(call.message.chat.id, text, reply_markup=markup)
            track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'poolswithpointsUmbra':
        top = TOP5('')
        poolsDict = top.topPointsPools('Umbra')
        poolsActivity = top.topPointsPoolsActivity('Umbra')
        tvlData = top.topPointsPooolsTVL('Umbra')
        if not poolsDict:
            bot.send_message(call.message.chat.id, "No Umbra Points pools found at the moment.")
            return
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"]
        for idx, (pair_and_yield, url) in enumerate(poolsDict.items()):
            activity = poolsActivity.get(pair_and_yield, "N/A")
            tvl = tvlData.get(pair_and_yield, "N/A")
            medal = medals[idx] if idx < len(medals) else ""
            try:
                a = float(activity)
                if a > 0.2:
                    activity_str = 'High ✅'
                elif a > 0.05:
                    activity_str = 'Moderate ⚠️'
                else:
                    activity_str = 'Low ‼️'
            except:
                activity_str = str(activity)
            text = f"{medal} {pair_and_yield}\nPool activity: {activity_str}\nTvl: 💲{tvl}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🌐 Go to the pool", url=url))
            msg = bot.send_message(call.message.chat.id, text, reply_markup=markup)
            track_user_msg(call.from_user.id, msg.message_id)

    
@bot.callback_query_handler(func=lambda call: call.data in ASSETS)
def pools_for_asset(call):
    asset = ASSETS[call.data]
    top = TOP5(asset)
    bestYield = top.theBestYield()
    poolsActivity = top.poolsActivity()
    tvlData = top.tvlData()
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for idx, (pair_and_yield, url) in enumerate(bestYield):
        activity = poolsActivity.get(pair_and_yield, "N/A")
        tvl = tvlData.get(pair_and_yield, "N/A")
        medal = medals[idx] if idx < len(medals) else ""
        try:
            a = float(activity)
            if a > 0.2:
                activity_str = 'High ✅'
            elif a > 0.05:
                activity_str = 'Moderate ⚠️'
            else:
                activity_str = 'Low ‼️'
        except:
            activity_str = str(activity)
        text = f"{medal} {pair_and_yield}\nPool activity: {activity_str}\nTvl: 💲{tvl}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🌐 Go to the pool", url=url))
        msg = bot.send_message(call.message.chat.id, text, reply_markup=markup)
        track_user_msg(call.from_user.id, msg.message_id)

@bot.message_handler(commands=['gsvm','gsvn','tableofcontents','feedback','restart'])
def handle_commands(message):
    command = message.text.split()[0].lstrip('/')
    user_id = message.from_user.id
    chat_id = message.chat.id

    if command == 'gsvm':
        track_user_msg(user_id, message.message_id)
        msg = bot.send_message(chat_id, 'GSVM fam 👋')
        track_user_msg(user_id, msg.message_id)
    elif command == 'gsvn':
        track_user_msg(user_id, message.message_id)
        msg = bot.send_message(chat_id, 'GSVN fam 🌃')
        track_user_msg(user_id, msg.message_id)
    elif command == 'tableofcontents':
        delete_user_msgs(chat_id, user_id)
        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass
    elif command == 'feedback':
        track_user_msg(user_id, message.message_id)
        markup = types.InlineKeyboardMarkup()
        urlX = 'https://x.com/lil_not_baby'
        urlTG = 'https://t.me/Eclipsinoor'
        markup.add(types.InlineKeyboardButton("My X 📱", url=urlX))
        markup.add(types.InlineKeyboardButton("My TG ➤", url=urlTG))
        msg = bot.send_message(
            chat_id,
            'Dear eFams, I will be happy to hear your honest opinion about eEconomist bot - that way you will direct me to improvements ☺️\nIf you\'re up for it, please send me a DM on X or my TG',
            reply_markup=markup
        )
        track_user_msg(user_id, msg.message_id)
    elif command == 'restart':
        # 1. Delete all user context messages
        delete_user_msgs(chat_id, user_id)

        # 2. Delete all permanent messages
        for msg_id in PERMANENT_MSG_IDS.get(user_id, []):
            try:
                bot.delete_message(chat_id, msg_id)
            except Exception:
                pass

        # 3. Delete sticky/menu image/messages from sticky-menu logic, if any
        for _id_dict in [MENU_IMAGE_ID, STICKY_MSG_ID, LAST_MENU_MSG_ID]:
            msg_id = _id_dict.get(user_id)
            if msg_id:
                try: bot.delete_message(chat_id, msg_id)
                except: pass
                _id_dict[user_id] = None

        # 4. Delete the restart command itself
        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass

        # 5. Reset ALL trackers for user
        USER_MSG_IDS[user_id] = []
        PERMANENT_MSG_IDS[user_id] = []
        MENU_IMAGE_ID[user_id] = None
        # These two might not exist but clear them if so:
        if 'STICKY_MSG_ID' in globals():
            STICKY_MSG_ID[user_id] = None
        if 'LAST_MENU_MSG_ID' in globals():
            LAST_MENU_MSG_ID[user_id] = None

        # 6. Show start screen again
        start(message)

@bot.message_handler(func=lambda m: True)
def handle_unexpected_message(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    # Optionally, delete user's message to keep chat clean
    try:
        bot.delete_message(chat_id, message.message_id)
    except Exception:
        pass

    # Send your polite nudge + link button
    markup = types.InlineKeyboardMarkup()
    url = 'https://turbogirleclipselive.azmth.ai/'
    markup.add(types.InlineKeyboardButton("Turbo Girl 👧", url=url))
    msg = bot.send_message(
        chat_id,
        text = "Hey eFam! Use the menu or button below to navigate the bot. eEconomist isn’t here for small talk 😅 but if you're feeling chatty, you can always take on Turbo Girl :)\nJust be warned… she will roast you 😉😈",
        reply_markup=markup
    )
    track_user_msg(user_id, msg.message_id)

bot.polling()











