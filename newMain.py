import telebot
from telebot import types
from TOP import TOP5
from Bitz import BITZ
from sBitz import sBITZ
import time
from threading import Lock
import threading

bot = telebot.TeleBot('7968913931:AAFrFTAOgxaiN4MoMOPhHJmk3o5qAnsgYNc')

TOP5_CACHE = {}  # { symbol: { 'obj': TOP5, 'time': timestamp } }
CACHE_TTL = 120
CACHE_LOCK = Lock()

# Tracking
USER_MSG_IDS = {}         # For context (yields, etc.)
PERMANENT_MSG_IDS = {}    # For all "permanent" UI messages
MENU_IMAGE_ID = {}        # Last sent menu image (book.png) per user
EARNING_STATE = set()
HOLDING_STATE = set()

# NEW: For sticky/menu messages sent from sticky button!
STICKY_MSG_ID = {}
LAST_MENU_MSG_ID = {}
POOL_MSG_IDS = {} 
LAST_TOP5_PER_GROUP = {}

ASSETS = {
    '$BITZ ⛏️': 'BITZ',
    '$sBITZ 💧': 'sBITZ',
    '$tUSD 💵': 'TUSD',
    '$tETH 💎': 'tETH',
    '$ETH 💎': 'ETH',
    '$USDC 💵': 'USDC',
    '$USDT 💵': 'USDT',
    '$SOL 🚀': 'SOL',
    '$LAIKA 🐶': 'LAIKA',
    '$ES 👑': 'ES'
}

POINTS = {
    'BITZ/ETH': 3456000,
    'sBITZ/ETH': 6048000,
    'SOL/USDC': 2160000,
    'ETH/USDC': 8640000,
    'SOL/ETH': 2592000,
    'tETH/ETH': 864000,
    'tUSD/USDC': 518400
}


SUBSCRIBERS_PER_GROUP = {}  # {group_id: set(user_ids)}

def pool_key(pool_string):
    # extract just the pool part, without APR
    return pool_string.split(' | ')[0].strip()

def notify_markup(user_id, group_id):
    markup = types.InlineKeyboardMarkup()
    if user_id in SUBSCRIBERS_PER_GROUP.get(group_id, set()):
        markup.add(types.InlineKeyboardButton("🔕 Unsubscribe", callback_data=f"unsubscribe_group:{group_id}"))
    else:
        markup.add(types.InlineKeyboardButton("🔔 Notify me of changes in this top", callback_data=f"notify_group:{group_id}"))
    return markup

def extract_pool_name(full_key):
    # Extracts "PAIR (DEX)" from "PAIR (DEX) | X.XXX％"
    return full_key.split(' | ')[0].strip()

@bot.callback_query_handler(func=lambda call: call.data.startswith("remove_notification:"))
def remove_notification(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

def track_pool_msg(user_id, msg_id):
    POOL_MSG_IDS.setdefault(user_id, []).append(msg_id)

def normalize_pool_name(name):
    return name.replace(' (Invariant)', '').strip().upper()

def maybe_notify_group(group_id, current_top5):
    global LAST_TOP5_PER_GROUP
    prev_top5 = LAST_TOP5_PER_GROUP.get(group_id)

    curr_keys = [pool_key(p) for p in current_top5]
    prev_keys = [pool_key(p) for p in prev_top5] if prev_top5 else []

    if prev_top5 is not None and curr_keys != prev_keys:
        prev_set = set(prev_keys)
        curr_set = set(curr_keys)

        added = [current_top5[i] for i, k in enumerate(curr_keys) if k not in prev_set]
        removed = [prev_top5[i] for i, k in enumerate(prev_keys) if k not in curr_set]
        moved = []
        for k in curr_set & prev_set:
            old_idx = prev_keys.index(k)
            new_idx = curr_keys.index(k)
            if old_idx != new_idx:
                moved.append((current_top5[new_idx], old_idx + 1, new_idx + 1))

        msg_lines = [f"🔔 <b>The Top 5 for {group_id.replace('top5_', '').upper()} has changed!</b>\n"]
        if added:
            msg_lines.append("🆕 <b>New pools entered:</b>")
            for pool in added:
                msg_lines.append(f"  • {pool}")
        if removed:
            msg_lines.append("❌ <b>Pools removed:</b>")
            for pool in removed:
                msg_lines.append(f"  • {pool}")
        if moved:
            msg_lines.append("🔄 <b>Pools changed position:</b>")
            for pool, old_pos, new_pos in moved:
                msg_lines.append(f"  • {pool}: {old_pos} → {new_pos}")

        msg_lines.append("\nCheck the latest Top 5 in the bot! 🏊‍♂️")

        # Add Remove button
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Remove", callback_data=f"remove_notification:{group_id}"))

        user_ids = SUBSCRIBERS_PER_GROUP.get(group_id, set())
        for user_id in user_ids:
            try:
                bot.send_message(
                    user_id,
                    "\n".join(msg_lines),
                    parse_mode='HTML',
                    reply_markup=markup
                )
            except Exception as e:
                print(f"Failed to notify {user_id}: {e}")

    LAST_TOP5_PER_GROUP[group_id] = current_top5

def get_top5(symbol):
    now = time.time()
    with CACHE_LOCK:
        cache_entry = TOP5_CACHE.get(symbol)
        if cache_entry and now - cache_entry['time'] < CACHE_TTL:
            return cache_entry['obj']
        top = TOP5(symbol)
        top.fetch_all()  # if needed
        TOP5_CACHE[symbol] = {'obj': top, 'time': now}
        return top
    
def cache_refresher():
    while True:
        with CACHE_LOCK:
            for symbol in list(TOP5_CACHE.keys()):
                top = TOP5(symbol)
                top.fetch_all()
                TOP5_CACHE[symbol] = {'obj': top, 'time': time.time()}

                # Check for top5 changes for each group
                # Overall
                if symbol == '':
                    group_id = "top5_overall"
                    current_top5 = [k for k, v in top.top5_pools_by_apy()]
                    maybe_notify_group(group_id, current_top5)
                # For each asset
                else:
                    group_id = f"top5_{symbol.upper()}"
                    current_top5 = [k for k, v in top.theBestYield()]
                    maybe_notify_group(group_id, current_top5)
        time.sleep(CACHE_TTL)

def is_nucleus_pool(pool_name):
    # Remove protocol suffix for matching
    base = pool_name.replace(' (Invariant)', '').strip()
    tokens = base.split('/')
    if len(tokens) != 2:
        return False
    pair_set = set([t.strip() for t in tokens])
    # These are the Nucleus pairs (regardless of order)
    return pair_set in [set(['tETH','ETH']), set(['tETH','USDC'])]

def sticky_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🦶 BACK'),types.KeyboardButton('Table of contents 📜'))
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
    HOLDING_STATE.discard(user_id)

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
    file = open('./bookaa.3.jpg', 'rb')
    photo_msg = bot.send_photo(chat_id, file)
    MENU_IMAGE_ID[user_id] = photo_msg.message_id
    PERMANENT_MSG_IDS.setdefault(user_id, []).append(photo_msg.message_id)

    # 2. Send menu message with keyboard
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton('Juiciest 🧃 liquidity pools 🏊🏻‍♂️', callback_data='yield')
    markup.row(button1)
    button2 =types.InlineKeyboardButton('$BITZ staking performance 🥩', callback_data='bitz')
    button3 =types.InlineKeyboardButton('$sBITZ HODL performance 💧', callback_data='sbitz')
    markup.row(button2,button3)
    button4 =types.InlineKeyboardButton('Cross-chain opportunities 🤞⛓️', callback_data='crosschain')
    button5 =types.InlineKeyboardButton('Retroactive points 🪂', callback_data='points')
    markup.row(button4,button5)
    button6 =types.InlineKeyboardButton('GameFi 🎮 & 💰', callback_data='gamefi')
    button7 =types.InlineKeyboardButton('NFTs 🖼', callback_data='nfts')
    markup.row(button6,button7)
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
        "Use the Menu or buttons below to navigate easily 🧭",
        reply_markup=sticky_menu_keyboard()
    )
    PERMANENT_MSG_IDS[user_id].append(sticky_msg.message_id)

    # Remove the "grab your" button
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except Exception:
        pass

@bot.message_handler(func=lambda m: m.text == 'Table of contents 📜')
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

@bot.message_handler(func=lambda m: m.text == '🦶 BACK')
def handle_back_button(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    pool_msgs = POOL_MSG_IDS.get(user_id, [])
    if pool_msgs:
        # Delete all pool messages
        for msg_id in pool_msgs:
            try:
                bot.delete_message(chat_id, msg_id)
            except Exception:
                pass
        # Remove pool message IDs from USER_MSG_IDS as well
        if user_id in USER_MSG_IDS:
            USER_MSG_IDS[user_id] = [mid for mid in USER_MSG_IDS[user_id] if mid not in pool_msgs]
        POOL_MSG_IDS[user_id] = []

        # Optionally, delete the BACK press message itself for cleanliness
        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass
        return  # Don't proceed to regular back logic

    # --- Default behavior (delete last non-permanent message) ---
    permanent = set(PERMANENT_MSG_IDS.get(user_id, []))
    user_msgs = USER_MSG_IDS.get(user_id, [])
    non_perm_msgs = [msg_id for msg_id in user_msgs if msg_id not in permanent]

    if non_perm_msgs:
        last_msg_id = non_perm_msgs[-1]
        try:
            bot.delete_message(chat_id, last_msg_id)
        except Exception:
            pass
        USER_MSG_IDS[user_id].remove(last_msg_id)
    else:
        msg = bot.send_message(chat_id, "No more messages to go back to 😜")
        track_user_msg(user_id, msg.message_id)

    # Optionally delete the Back button press itself
    try:
        bot.delete_message(chat_id, message.message_id)
    except Exception:
        pass

# ---- Menu Handlers for yield/other_chapters ----

@bot.callback_query_handler(func=lambda call: call.data in ['yield', 'points', 'crosschain','gamefi','bitz', 'sbitz', 'nfts'])
def handle_menu(call):
    if call.data == 'yield':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Juciest pools 👉 overall', callback_data='overall'))
        markup.add(types.InlineKeyboardButton('Juciest pools 👉 for particular asset', callback_data='particular'))
        msg = bot.send_message(call.message.chat.id, "Choose pool group fam 🤔", reply_markup=markup)
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'points':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Invariant 🔱', callback_data='invariant'))
        markup.add(types.InlineKeyboardButton('Astrol 🔷', callback_data='astrol'))
        markup.add(types.InlineKeyboardButton('Deserialize 🆕', callback_data='deserialize'))
        markup.add(types.InlineKeyboardButton('Umbra 🃏', callback_data='umbra'))
        markup.add(types.InlineKeyboardButton('EnsoFi ❇️', callback_data='ensofi'))
        markup.add(types.InlineKeyboardButton('AllDomains 🧘‍♂️', callback_data='alldomains'))
        markup.add(types.InlineKeyboardButton('Turbo Girl 💋', callback_data='turbogirl'))
        msg = bot.send_message(call.message.chat.id, "Choose DApp to earn retroactive points using your assets, fam 🎯\n\nNever underestimate ecosystem drops especially on Eclipse 🙃", reply_markup=markup)
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'crosschain':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Hyperlane ⏩', callback_data='hyperlane'))
        markup.add(types.InlineKeyboardButton('Deserialize 🔝', callback_data='deserialize'))
        markup.add(types.InlineKeyboardButton('Relay 🕺', callback_data='relay'))
        markup.add(types.InlineKeyboardButton('More to come 🔜',callback_data='disabled'))
        msg = bot.send_message(call.message.chat.id,"<b>Retroactive</b> cross-chain interactions like 🌉 between Eclipse and other block⛓️s", parse_mode='html', reply_markup=markup)
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'bitz':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('APR data 📊', callback_data='stacking'))
        markup.add(types.InlineKeyboardButton('Calculate yield estimates 🧮', callback_data='earning'))
        msg = bot.send_message(call.message.chat.id,"Explore incredible <b>$BITZ</b> upside🔋", parse_mode='html', reply_markup=markup)
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'sbitz':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('APY data 📊', callback_data='compounding'))
        markup.add(types.InlineKeyboardButton('Calculate yield estimates 🧮', callback_data='searning'))
        msg = bot.send_message(call.message.chat.id,"Explore incredible <b>$sBITZ</b> upside🔋", parse_mode='html', reply_markup=markup)
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'gamefi':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Werm 🪱', callback_data='werm'))
        markup.add(types.InlineKeyboardButton('Cryptara 🏰', callback_data='cryptara'))
        markup.add(types.InlineKeyboardButton('Doiq 🏆', callback_data='doiq'))
        msg = bot.send_message(call.message.chat.id,"Have fun and compete for the <b>real rewards</b> 💰 with eGaming on <strong>Eclipse</strong> 💫", parse_mode='html', reply_markup=markup)
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'nfts':
        markup = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton('👑 ASC 👑', callback_data='asc')
        markup.row(button)
        button1 = types.InlineKeyboardButton('🥇 Validators', callback_data='validators')
        button2 = types.InlineKeyboardButton('🥈 E-Lander', callback_data='elander')
        markup.row(button1,button2)
        button3 = types.InlineKeyboardButton('🥉 Celestial Mammoth', callback_data='celestial')
        button4 = types.InlineKeyboardButton('🥉 Eclipse Bulls Club', callback_data='ebc')
        markup.row(button3,button4)
        button5 = types.InlineKeyboardButton('🥉 Sunborn', callback_data='sunborn')
        button6 = types.InlineKeyboardButton('🥉 Moon Odyssey Club', callback_data='moc')
        markup.row(button5,button6)
        button7 = types.InlineKeyboardButton('🥉 NeuroGuardians', callback_data='neuroGuardians')
        button8 = types.InlineKeyboardButton('🥉 Solar Companions', callback_data='sc')
        markup.row(button7,button8)
        msg = bot.send_message(call.message.chat.id,"Here is <b>my current top</b> NFT collections on Eclipse 🌃\n\nSome already offer <em>utilities and ecosystem bonuses</em>, while others might in the future. Remember, NFTs are <b>highly volatile</b> and risky - <em>read each description</em> carefully and <b>DYOR</b> 🕵️‍♀️", parse_mode='html', reply_markup=markup)
        track_user_msg(call.from_user.id, msg.message_id)
    else:
        msg = bot.send_message(call.message.chat.id, "Coming tho0on!")
        track_user_msg(call.from_user.id, msg.message_id)
    
@bot.callback_query_handler(func=lambda call: call.data == 'disabled')
def disabled_callback(call):
    bot.answer_callback_query(call.id, "Coming soon 🚧", show_alert=False)

@bot.callback_query_handler(func=lambda call: call.data in ['particular', 'overall'])
def handle_juciestpools(call):
    if call.data == 'particular':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('eEconomy pillars 🏛: $ES, $BITZ and etc.', callback_data='pillars'))
        markup.add(types.InlineKeyboardButton('Other assets 📊: $ETH, $SOL and etc.', callback_data='other_assets'))
        msg = bot.send_message(call.message.chat.id, "Choose pool group fam 🤔", reply_markup=markup)
        track_user_msg(call.from_user.id, msg.message_id)

    elif call.data == 'overall':
        top = get_top5('')
        bestYield = top.top5_pools_by_apy()
        if not bestYield:
            msg = bot.send_message(call.message.chat.id, "No juicy pools found across all DEXes.")
            track_user_msg(call.from_user.id, msg.message_id)
            return

        # Use the smart TVL/activity map from the updated TOP5!
        tvl_activity_map = top.tvl_activity_for_overall()

        tvl_activity_by_pool = {}
        for k, v in tvl_activity_map.items():
            base_pool = extract_pool_name(k)
            tvl_activity_by_pool[base_pool] = v

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for idx, (pair_and_yield, url) in enumerate(bestYield):
            if ' | ' not in pair_and_yield:
                continue

            pool_name, yield_part = pair_and_yield.split(' | ', 1)

            display_pool_name = pool_name
            tvl, activity = tvl_activity_by_pool.get(display_pool_name, ("N/A", "N/A"))

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

            points = None
            norm_pool_name = normalize_pool_name(pool_name)
            for key in POINTS:
                if normalize_pool_name(key) == norm_pool_name:
                    points = POINTS[key]
                    break

            text = f"{medal} {display_pool_name} | {yield_part} (24H)\nPool activity: {activity_str}\nTvl: 💲{tvl}"
            if points:
                text += f"\nPoints 24H: 🎯 {points}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🌐 Go to the pool", url=url))
            msg = bot.send_message(call.message.chat.id, text, reply_markup=markup)
            track_pool_msg(call.from_user.id, msg.message_id)
            track_user_msg(call.from_user.id, msg.message_id)
        group_id = "top5_overall"  # Or e.g. f"top5_{asset}"
        markup = notify_markup(call.from_user.id, group_id)
        msg = bot.send_message(call.message.chat.id,
            "Want instant alerts when this top changes? Click the bell ⤵️",
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)
        track_pool_msg(call.from_user.id, msg.message_id)



@bot.callback_query_handler(func=lambda call: call.data in ['stacking', 'earning'])
def handle_bitz(call):
    if call.data == 'stacking':
        bitz = BITZ()
        dataBout24H = bitz.findOutApr()
        dataAnnual = bitz.annualAPR()
        msg = bot.send_message(
            call.message.chat.id,
            f'$BITZ 24H APR:\n✅{dataBout24H}％\n\n$BITZ annual APR:\n✅{dataAnnual}％',
            parse_mode='html',
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'earning':
        EARNING_STATE.add(call.from_user.id)
        msg = bot.send_message(call.message.chat.id, 'Enter the number of $BITZ you wanna stake, fam: ')
        track_user_msg(call.from_user.id, msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data in ['compounding', 'searning'])
def handle_bitz(call):
    if call.data == 'compounding':
        sbitz = sBITZ()
        dataBout24H = sbitz.calculate_daily_compounding_yield()
        dataAnnual = sbitz.calculate_apy()
        msg = bot.send_message(
            call.message.chat.id,
            f'$sBITZ 24H APY:\n✅{dataBout24H}％\n\n$sBITZ annual APY:\n✅{dataAnnual}％',
            parse_mode='html',
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'searning':
        HOLDING_STATE.add(call.from_user.id)
        msg = bot.send_message(call.message.chat.id, 'Enter the number of $sBITZ you gonna hold, fam: ')
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

@bot.message_handler(func=lambda m: m.from_user.id in HOLDING_STATE)
def get_potentialHoldings(message):
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
    sbitz = sBITZ()
    forDay = sbitz.howMuchEarnDaily(staked)
    forWeek = sbitz.howMuchEarnWeekly(staked)
    forMonth = sbitz.howMuchEarnMonthly(staked)
    forYear = sbitz.howMuchYearly(staked)
    msg = bot.send_message(
        message.chat.id,
        f'Lets see fam how much $sBITZ you will earn 👀\n\n💹{forDay}\n💹{forWeek}\n💹{forMonth}\n💹{forYear}')
    track_user_msg(user_id, msg.message_id)
    # Remove user from earning state
    HOLDING_STATE.discard(user_id)

@bot.callback_query_handler(func=lambda call: call.data in ['pillars', 'other_assets'])
def handle_asset_group(call):
    if call.data == 'pillars':
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("$ES 👑", callback_data="$ES 👑")
        markup.row(button1)
        button2 = types.InlineKeyboardButton("$BITZ ⛏️", callback_data="$BITZ ⛏️")
        button3 = types.InlineKeyboardButton("$sBITZ 💧", callback_data="$sBITZ 💧")
        markup.row(button2,button3)
        button4 = types.InlineKeyboardButton("$tUSD 💵", callback_data="$tUSD 💵")
        button5 = types.InlineKeyboardButton("$tETH 💎", callback_data="$tETH 💎")
        markup.row(button4,button5)
        msg = bot.send_message(
            call.message.chat.id,
            "Choose one asset you want to earn with as a smart eEconomist 😉",
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)

    elif call.data == 'other_assets':
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("$ETH 💎", callback_data="$ETH 💎")
        markup.row(button1)
        button2 = types.InlineKeyboardButton("$USDC 💵", callback_data="$USDC 💵")
        button3 = types.InlineKeyboardButton("$USDT 💵", callback_data="$USDT 💵")
        markup.row(button2,button3)
        button4 = types.InlineKeyboardButton("$SOL 🚀", callback_data="$SOL 🚀")
        button5 = types.InlineKeyboardButton("$LAIKA 🐶", callback_data="$LAIKA 🐶")
        markup.row(button4,button5)
        msg = bot.send_message(
            call.message.chat.id,
            "Choose one asset you want to earn with as a smart eEconomist 😉",
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data in ['hyperlane', 'relay', 'deserialize'])
def handle_bridges_group(call):
    if call.data == 'hyperlane':
        markup = types.InlineKeyboardMarkup()
        url = 'https://www.usenexus.org/?origin=eclipsemainnet&destination=solanamainnet'
        markup.add(types.InlineKeyboardButton("Lets do some hyper-fast 🌉ing", url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "Although Hyperlane has already held its TGE, they’ll be distributing $HYPER rewards quarterly 😉\n\nTo be eligible you need to <b>spend $3 in Hyperlane fees</b> and the nearest snaphot will be <b>in the end of Q3</b> ish\n\nRoute instance: Solana 🔁 Eclipse (USDC & SOL)",
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
    elif call.data == 'deserialize':
        markup = types.InlineKeyboardMarkup()
        url = 'https://bridge.deserialize.xyz/'
        markup.add(types.InlineKeyboardButton("Do some 🌉ing on Deserialize", url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "Cheap, reliable and fast cross-chain bridge supporting plenty of chains 👑\n\nSo far I didn't see info that points can be earned by bridging as well but <em>stay tuned</em> fams ⚠️",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)


@bot.callback_query_handler(func=lambda call: call.data in ['werm', 'cryptara', 'doiq'])
def handle_games_group(call):
    if call.data == 'werm':
        markup = types.InlineKeyboardMarkup()
        url = 'https://werm.fun/'
        markup.add(types.InlineKeyboardButton("Play Werm 🎮", url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "Werm is a game that's quickly become an eCommunity favorite, embodying the competitive spirit of Web3 for many eFams 🤺\n\nParticipate in tournaments (entry fee required) and <b>win or lose some $</b> based on your performance\n\nIn short: the better you play - the more you earn, fam 😏",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'cryptara':
        markup = types.InlineKeyboardMarkup()
        url = 'https://eclipse.cryptara.world/'
        markup.add(types.InlineKeyboardButton("Play Cryptara 🎮", url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "Cryptara Conquest is an adrenaline-packed sci-fi bullet-hell survival game where strategy and sharp reflexes lead to victory ⚔️\n\nCryptara is tough but what could be better for gamers who thrive on a challenge? 😉\n\nRise to the top of the leaderboard and claim your share of the $LAIKA and $BITZ prize pool 🤑 (including real-time dungeon loot in $LAIKA)",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'doiq':
        markup = types.InlineKeyboardMarkup()
        url = 'https://doiq.xyz/'
        markup.add(types.InlineKeyboardButton("Play doiq 🎮", url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "A 90s retro social RPG morphing memes & speculation. Battle, shop, craft, bet & rob players to thrive 😜\n\nNot long ago, they hosted the BABY CUP - fewer participants but a <b>solid prize pool</b>, giving winners great odds 😼\n\n<b>Earn pineapples</b> (the base currency of the game). Pineapples are then used for upgrades, skills, items, casino games, evolving into one of three character paths and so much more ✍️",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)



@bot.callback_query_handler(func=lambda call: call.data in ['asc', 'validators', 'elander','celestial','ebc','sunborn','moc','neuroGuardians','sc'])
def handle_games_group(call):
    if call.data == 'asc':
        markup = types.InlineKeyboardMarkup()
        url = 'https://afterschoolclub.xyz/'
        markup.add(types.InlineKeyboardButton("Head over ASC 🌐", url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "ASC is literally the <b>Official Genesis NFT Collection of Eclipse</b>\n\nWithin the Eclipse economy, it serves both as an <b>identity layer and a luxury item</b>. The fact that some people rock fake ASC PFP speaks volumes 😉\n\nASC holders always enjoy exclusive <b>bonuses and privileges</b> across ecosystem projects - including <em>WLs (cross-chain too), early access, extra points, and multipliers</em> 🎇\n\nIf wanna be a true Eclipse-maxi, grabbing an ASC should be your #1 priority 💯",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'validators':
        markup = types.InlineKeyboardMarkup()
        url = 'https://linktr.ee/validators'
        markup.add(types.InlineKeyboardButton("Head over Validators 🌐", url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "Validators is <b>the first NFT collection on Eclipse</b> SVM, and first across Solana, Ethereum, Celestia 🚀\n\nImo this is the second largest, most influential and most popular collection on Eclipse 🔥 Validators holders recieve <b>a lot of bonuses</b> across Eclipse ecosystem like <em>WLs, extra points, and multipliers</em> 🎯\n\nIf you <em>believe in something,</em> then holding Validators is a must - you cant afford to skip it 🛸",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'elander':
        markup = types.InlineKeyboardMarkup()
        url = 'https://e-lander.xyz/'
        markup.add(types.InlineKeyboardButton("Head over eLander 🌐", url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "E-Lander gives you access to a private DeFi community where people share alpha (insights), find the best strategies to <b>earn, and grow</b> together 🍃\n\nOwning an E-Lander NFT is more than just joining a group - it gives you <em>real benefits inside the EnsoFi ecosystem</em>\n\nAs a holder <b>you will get</b>: exclusive airdrops, point boosts, fee discounts and access to earning vaults\n\nAs EnsoFi grows, E-Lander holders will continue to unlock <em>more features, special rewards, and possibly take part in future governance</em> - bullish 📈",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'celestial':
        markup = types.InlineKeyboardMarkup()
        url = 'https://linktr.ee/celestialmmammoth'
        markup.add(types.InlineKeyboardButton("Celestial 🌐", url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "CelestialMammoth is the <b>Genesis NFT Collection</b> within CELESTIAL ecosystem on Eclipse 😎\n\nIt grants membership to an <b>exclusive community</b>, offering <b>bonuses</b> like <em>WLs, points, and multipliers</em> from partners such as Invariant, Umbra, and more 🤝",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'ebc':
        markup = types.InlineKeyboardMarkup()
        url = 'https://x.com/ebclubnft'
        markup.add(types.InlineKeyboardButton("Head over ECB X 🌐", url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "EBC is a collection of bulls that live at the intersection of two universes on the Eclipse 🪐\n\nThis collection is a quite popular within eCommunity, there are many top Gs among its holders. Nowadays bulls remain active as well as promising 🤞\n\nRecently they partnered with Turbo Girl, so the bulls holders can receive <b>a boost</b> in the Proof of Love campaign 💋",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'sunborn':
        markup = types.InlineKeyboardMarkup()
        url = 'https://x.com/sunborn_art'
        markup.add(types.InlineKeyboardButton("Head over Sunborn X 🌐", url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "Sunborn is the vibrant  <b>art cult</b> on Eclipse 🎨\n\nThey host frequent Discord events, including painting competitions where artists can earn both <b>recognition and cash prizes</b> 💰\n\nSunborn also collaborates with other ecosystem projects. A recent highlight is the Turbo Girl partnership, where Sunborn holders receive <b>a boost</b> in the Proof of Love campaign 💋",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'moc':
        markup = types.InlineKeyboardMarkup()
        url = 'https://x.com/Moonlaunchfun'
        markup.add(types.InlineKeyboardButton("Head over MoonLaunch X 🌐", url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "Moon Odyssey Club is an pixel-style PFP collection of moon-inspired characters from MoonLaunch - a platform where anyone can create their own token 🌘\n\nThe collection has been inactive for quite some time, mirroring MoonLaunch itself, which has resulted in a very low floor price rn 📉\n\nHowever, there is still potential for a strong comeback, thanks to an ongoing collaboration with the AllDomains project and the chance to earn extra <b>AllDomains points</b> by holding MOC 🐵",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'neuroGuardians':
        markup = types.InlineKeyboardMarkup()
        url = 'https://x.com/NeuroGuardians'
        markup.add(types.InlineKeyboardButton("Head over NeuroGuardians X 🌐", url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "NeuroGuardians is a collection of 888 unique characters that players can use in NeuroGuardians game 🎮\n\nThis NFT offers great benefits for gamers, including unique characters and boosts that help climb the leaderboard and earn juicy rewards 😋\n\nEarly minters have already more than paid off, and with the collection currently at a low, the upside potential is huge. Plus, it features ecosystem collaborations and a cross-chain partnership with MegaETH 🥕",
            parse_mode='html',
            reply_markup=markup
        ) 
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'sc':
        markup = types.InlineKeyboardMarkup()
        url = 'https://linktr.ee/solardexofficial'
        markup.add(types.InlineKeyboardButton("Head over Solar Dex🌐", url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "Solar Companions is an NFT collection centered around the upcoming Solar Companion Mobile App 📱\n\nHolders can expect future bonuses and utilities on the platform. Recently, Solar Studios has become noticeably more active - great news for current holders and a strong signal for those yet to grab one 💡\n\nWith recent activities and collaborations across Solana and Aurora ecosystems, the collection looks very promising rn ⚖️",
            parse_mode='html',
            reply_markup=markup
        )    
        track_user_msg(call.from_user.id, msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data in ['invariant', 'umbra', 'astrol', 'alldomains', 'ensofi', 'deserialize','turbogirl'])
def handle_DApps_group(call):
    if call.data == 'invariant':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Pools with points 🔱', callback_data='poolswithpointsInvariant'))
        msg = bot.send_message(
            call.message.chat.id,
            "<em>Provide liquidity</em> to the pools and earn <strong>Invariant Points</strong> ✅\n\nRank at the top of the leaderboard to unlock <strong>points</strong> in other ecosystem projects too <em>(EDAS, EnsoFi, AllDomains and Nucleus)</em> 🎇",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'umbra':
        url = 'https://lunarfinance.io/swap'
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Trade on Lunar Finance 🌒', url=url))
        markup.add(types.InlineKeyboardButton('Pools with points 🃏', callback_data='poolswithpointsUmbra'))
        msg = bot.send_message(
            call.message.chat.id,
            "1) Umbra x Lunar Finance just launched a 4-week <b>Nitro Rush campaign</b> 🏎🔥\n\nEarn <b>Nitro XP</b> simply by trading on Lunar Finance and selecting Umbra as your route 🛣\n Nitro XP will be converted to <b>veUMBRA</b> at TGE 🪂 \n\n2) <em>Add liquidity</em> to earn <strong>Umbra Points</strong> instead of fees + earn extra points based on <em>swap volume</em> 🧪\n\nNote: Epoch 7 has ended, so points distribution for activites above is <b>currently paused</b> ⏸️",
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
    elif call.data == 'deserialize':
        url = 'https://www.deserialize.xyz/'
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Forward to Deserialize 🔝', url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "Deserialize is the best Dex Aggregator for the eCommunity!\n\nRecently they have added <b>points system</b> 🔥 To earn points you simply need to swap your assets 🔁",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)
    elif call.data == 'turbogirl':
        url = 'https://turbogirleclipselive.azmth.ai/'
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Get roasted by eGirl 🧎‍♂️‍➡️', url=url))
        msg = bot.send_message(
            call.message.chat.id,
            "Share a slice of the <b>25M SAI Points</b> pie just by <em>calling and chatting</em> with Turbo Girl AI 📞✨\n\nNo need to flex your wallet here, just <strong>flirt to earn</strong> 😏",
            parse_mode='html',
            reply_markup=markup
        )
        track_user_msg(call.from_user.id, msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data in ['poolswithpointsInvariant', 'poolswithpointsUmbra'])
def handle_poolswithpoints(call):
    if call.data == 'poolswithpointsInvariant':
        top = get_top5('points-invariant')
        poolsDict = top.topPointsPools('Invariant')
        poolsActivity = top.topPointsPoolsActivity('Invariant')
        tvlData = top.topPointsPooolsTVL('Invariant')
        if not poolsDict:
            bot.send_message(call.message.chat.id, "No Invariant Points pools found at the moment.")
            return
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]
        for idx, (pair_and_yield, url) in enumerate(poolsDict.items()):
            # Only support ' | ' as separator!
            if ' | ' not in pair_and_yield:
                continue  # skip weird keys

            pool_name, yield_part = pair_and_yield.split(' | ', 1)
            orig_pair_and_yield = pair_and_yield  # for correct lookups

            # Nucleus pool visual, but KEEP orig_pair_and_yield for lookup!
            display_pool_name = pool_name
            if is_nucleus_pool(pool_name):
                display_pool_name += ' ➕ Nucleus Points'

            activity = poolsActivity.get(orig_pair_and_yield, "N/A")
            tvl = tvlData.get(orig_pair_and_yield, "N/A")
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

            points = None
            norm_pool_name = normalize_pool_name(pool_name)
            for key in POINTS:
                if normalize_pool_name(key) == norm_pool_name:
                    points = POINTS[key]
                    break

            # Compose display with correct separator!
            text = f"{medal} {display_pool_name} | {yield_part}\nPool activity: {activity_str}\nTvl: 💲{tvl}"
            if points:
                text += f"\nPoints 24H: 🎯 {points}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🌐 Go to the pool", url=url))
            msg = bot.send_message(call.message.chat.id, text, reply_markup=markup)
            track_pool_msg(call.from_user.id, msg.message_id)
            track_user_msg(call.from_user.id, msg.message_id)

    elif call.data == 'poolswithpointsUmbra':
        top = get_top5('points-umbra')
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
            text = f"{medal} <b>{pair_and_yield}</b> (24H)\n<b>Pool activity</b>: {activity_str}\n<b>Tvl</b>: 💲{tvl}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🌐 Go to the pool", url=url))
            msg = bot.send_message(call.message.chat.id, text, parse_mode="HTML", reply_markup=markup)
            track_pool_msg(call.from_user.id, msg.message_id)
            track_user_msg(call.from_user.id, msg.message_id)


    
@bot.callback_query_handler(func=lambda call: call.data in ASSETS)
def pools_for_asset(call):
    asset = ASSETS[call.data]
    top = get_top5(asset)
    bestYield = top.theBestYield()
    try:
        bestYield = top.theBestYield()
    except Exception as e:
        print(f"Error in theBestYield for {asset}: {e}")
        bestYield = []
    if not bestYield:
        if asset == 'ES':
            msg = bot.send_message(call.message.chat.id, "No pools for $ES so far. Stay tuned for updates!")
        else:
            msg = bot.send_message(call.message.chat.id, "No pools found for this asset.")
        track_user_msg(call.from_user.id, msg.message_id)
        return
    poolsActivity = top.poolsActivity()
    tvlData = top.tvlData()
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for idx, (pair_and_yield, url) in enumerate(bestYield):  # <-- FIXED LINE
        # Only support ' | ' as separator!
        if ' | ' not in pair_and_yield:
            continue  # skip weird keys

        pool_name, yield_part = pair_and_yield.split(' | ', 1)
        orig_pair_and_yield = pair_and_yield  # for correct lookups

        # Nucleus pool visual, but KEEP orig_pair_and_yield for lookup!
        display_pool_name = pool_name
        if is_nucleus_pool(pool_name):
            display_pool_name += ' ➕ Nucleus Points 😍'

        activity = poolsActivity.get(orig_pair_and_yield, "N/A")
        tvl = tvlData.get(orig_pair_and_yield, "N/A")
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

        points = None
        norm_pool_name = normalize_pool_name(pool_name)
        for key in POINTS:
            if normalize_pool_name(key) == norm_pool_name:
                points = POINTS[key]
                break

        # Compose display with correct separator!
        text = f"{medal} {display_pool_name} | {yield_part} (24H)\nPool activity: {activity_str}\nTvl: 💲{tvl}"
        if points:
            text += f"\nPoints 24H: 🎯 {points}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🌐 Go to the pool", url=url))
        msg = bot.send_message(call.message.chat.id, text, reply_markup=markup)
        track_pool_msg(call.from_user.id, msg.message_id)
        track_user_msg(call.from_user.id, msg.message_id)
    group_id = f"top5_{asset.upper()}"   # Or e.g. f"top5_{asset}"
    markup = notify_markup(call.from_user.id, group_id)
    msg = bot.send_message(call.message.chat.id,
        "Want instant alerts when this top changes? Click the bell ⤵️",
        reply_markup=markup
    )
    track_user_msg(call.from_user.id, msg.message_id)
    track_pool_msg(call.from_user.id, msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("notify_group:"))
def subscribe_to_group(call):
    user_id = call.from_user.id
    group_id = call.data[len("notify_group:"):]
    SUBSCRIBERS_PER_GROUP.setdefault(group_id, set()).add(user_id)
    bot.answer_callback_query(call.id, "You will be notified of changes in this Top list!", show_alert=False)
    # Update button to show "Unsubscribe"
    markup = notify_markup(user_id, group_id)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("unsubscribe_group:"))
def unsubscribe_from_group(call):
    user_id = call.from_user.id
    group_id = call.data[len("unsubscribe_group:"):]
    SUBSCRIBERS_PER_GROUP.setdefault(group_id, set()).discard(user_id)
    bot.answer_callback_query(call.id, "You will no longer get notifications from this Top list.", show_alert=False)
    # Update button to show "Notify me"
    markup = notify_markup(user_id, group_id)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)


@bot.message_handler(commands=['gsvm','gsvn','tableofcontents','feedback','restart','back'])
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
    elif command == 'back':
        handle_back_button(message)
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
        text = "Hey eFam! Use the menu or buttons below to navigate the bot. eEconomist isn’t here for small talk 😅 but if you're feeling chatty, you can always take on <b>Turbo Girl</b> :)\n\nJust be warned… she will roast you 😉😈",
        parse_mode='HTML',
        reply_markup=markup
    )
    track_user_msg(user_id, msg.message_id)

threading.Thread(target=cache_refresher, daemon=True).start()
bot.polling()











