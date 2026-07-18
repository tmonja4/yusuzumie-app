import streamlit as st
from datetime import datetime

# 自動更新用の拡張機能を読み込み（インストールされていない場合はエラーを回避）
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

# --- 1. データベース設定 ---
@st.cache_resource
def get_database():
    return {"orders": [], "order_count": 0}

db = get_database()

st.set_page_config(page_title="模擬店オーダーシステム", page_icon="🍔", layout="wide")

MENU = [
    "🥤【ドリンク】スムージー", "🍋【ドリンク】レモネード", 
    "🍡【甘味】みたらし団子", "🍧【甘味】あんみつ", "🍌【甘味】チョコバナナ",
    "🍗【つまみ】から揚げ", "🍟【つまみ】ポテト", "🌭【つまみ】フランクフルト", 
    "🫛【つまみ】枝豆", "🥒【つまみ】きゅうり一本漬け"
]

mode = st.sidebar.radio("役割（画面）を選んでください", ["🛒 受付（レジ）", "🍳 調理場（キッチン）", "🏃 配達係（デリバリー）"])

# ==========================================
# 🛒 受付（レジ）画面
# ==========================================
if mode == "🛒 受付（レジ）":
    st.title("🛒 受付レジ画面")

    with st.expander("⚙️ システム設定（危険）"):
        if st.button("⚠️ 注文番号と履歴をすべて「1」からリセットする"):
            db["order_count"] = 0
            db["orders"] = []
            if "cart" in st.session_state:
                st.session_state.cart = {}
            st.success("すべてのデータをリセットしました！")
            st.rerun()

    if "cart" not in st.session_state:
        st.session_state.cart = {}

    st.subheader("1. 注文を入力")
    cols = st.columns(2)
    for i, item in enumerate(MENU):
        with cols[i % 2]:
            if st.button(item, use_container_width=True):
                st.session_state.cart[item] = st.session_state.cart.get(item, 0) + 1

    st.divider()

    st.subheader("2. カートの確認")
    cart_items = {k: v for k, v in st.session_state.cart.items() if v > 0}

    if len(cart_items) > 0:
        for item, count in cart_items.items():
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.markdown(f"#### {item}： **{count}** 個")
            with col2:
                if st.button("➖", key=f"minus_{item}"):
                    st.session_state.cart[item] -= 1
                    st.rerun()
            with col3:
                if st.button("➕", key=f"plus_{item}"):
                    st.session_state.cart[item] += 1
                    st.rerun()

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 注文を送信", type="primary", use_container_width=True):
                db["order_count"] += 1
                new_order = {
                    "id": db["order_count"],
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "items": cart_items.copy(),
                    "status": "調理待ち", 
                    "is_revised": False,
                    "diff_msg": ""
                }
                db["orders"].insert(0, new_order)
                st.session_state.cart = {}
                st.success(f"【 {new_order['id']} 番 】を送信しました！")
                st.rerun()
        with col_btn2:
            if st.button("🗑️ カートを空にする", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()
    else:
        st.info("商品は選択されていません。")

    st.divider()

    st.subheader("📝 注文状況・訂正")
    if not db["orders"]:
        st.write("送信された注文はありません。")
    else:
        for order in db["orders"]:
            if order["status"] == "配達完了":
                with st.expander(f"✅ 注文番号 {order['id']} : 配達完了"):
                    for item, count in order["items"].items():
                        st.write(f" - {item} : {count}個")
            else:
                with st.expander(f"注文番号 {order['id']} (現在の状態: {order['status']}) を訂正"):
                    edit_key = f"edit_{order['id']}"
                    if edit_key not in st.session_state:
                        st.session_state[edit_key] = order["items"].copy()

                    st.write("▼数量を変更して「訂正を送信」を押してください")
                    for item in MENU:
                        current_val = st.session_state[edit_key].get(item, 0)
                        if current_val > 0 or st.checkbox(f"{item} を追加", key=f"chk_{order['id']}_{item}"):
                            c1, c2 = st.columns([3, 1])
                            with c1:
                                st.write(item)
                            with c2:
                                new_val = st.number_input("個数", min_value=0, value=current_val, key=f"num_{order['id']}_{item}")
                                st.session_state[edit_key][item] = new_val

                    if st.button("🔄 この内容で訂正を送信", key=f"btn_edit_{order['id']}", type="primary"):
                        old_items = order["items"].copy()
                        new_items = {k: v for k, v in st.session_state[edit_key].items() if v > 0}

                        diffs = []
                        all_keys = set(old_items.keys()) | set(new_items.keys())
                        for k in all_keys:
                            old_v = old_items.get(k, 0)
                            new_v = new_items.get(k, 0)
                            if old_v != new_v:
                                if new_v == 0: diffs.append(f"❌ {k} (削除)")
                                elif old_v == 0: diffs.append(f"➕ {k} (追加: {new_v}個)")
                                else: diffs.append(f"🔄 {k} ({old_v}個 ➡️ {new_v}個)")

                        if diffs:
                            order["items"] = new_items
                            order["is_revised"] = True
                            order["diff_msg"] = "\n".join(diffs)
                            order["status"] = "調理待ち" 
                            st.success("訂正を送信しました！")
                            st.rerun()
                        else:
                            st.warning("変更がありませんでした。")

# ==========================================
# 🍳 調理場（キッチン）画面
# ==========================================
elif mode == "🍳 調理場（キッチン）":
    st.title("🍳 調理場画面")

    # --- 自動更新の設定 ---
    if st_autorefresh:
        st_autorefresh(interval=5000, key="kitchen_refresh") # 5000ミリ秒（5秒）ごとに更新
    else:
        st.warning("⚠️ 自動通知機能を使うには、ターミナルで `pip install streamlit-autorefresh` を実行してください。")

    # --- 新規注文・訂正の通知ロジック ---
    current_kitchen_state = {o["id"]: o["is_revised"] for o in db["orders"] if o["status"] == "調理待ち"}

    if "known_kitchen_state" not in st.session_state:
        st.session_state.known_kitchen_state = current_kitchen_state.copy()

    for oid, is_rev in current_kitchen_state.items():
        if oid not in st.session_state.known_kitchen_state:
            st.toast(f"🔔 新規注文（番号: {oid}）が入りました！", icon="🔥")
        elif is_rev and not st.session_state.known_kitchen_state[oid]:
            st.toast(f"⚠️ 注文番号 {oid} に訂正が入りました！", icon="⚠️")

    st.session_state.known_kitchen_state = current_kitchen_state.copy()

    # --- 画面表示 ---
    if st.button("🔄 最新の注文を手動で確認する", use_container_width=True):
        st.rerun()

    tab1, tab2 = st.tabs(["🔥 調理待ち", "✅ 調理完了リスト"])

    with tab1:
        active_orders = sorted([o for o in db["orders"] if o["status"] == "調理待ち"], key=lambda x: x["id"])

        if len(active_orders) == 0:
            st.success("現在、調理待ちの注文はありません！🎉")
        else:
            for o in active_orders:
                if o["is_revised"]:
                    st.error("⚠️ 【訂正が入りました！】")
                    st.markdown(f"**変更内容:**\n{o['diff_msg']}")

                with st.container(border=True):
                    st.markdown(f"# 🧾 番号: {o['id']}")
                    st.write(f"時間: {o['time']}")

                    for item, count in o["items"].items():
                        st.markdown(f"### 🔸 {item} ： **{count}** 個")

                    if st.button(f"✅ 調理完了（配達係へ回す）", key=f"kitchen_done_{o['id']}", type="primary", use_container_width=True):
                        o["status"] = "配達待ち"
                        o["is_revised"] = False 
                        st.rerun()
                st.write("") 

    with tab2:
        done_orders = [o for o in db["orders"] if o["status"] in ["配達待ち", "配達中", "配達完了"]]
        if not done_orders:
            st.write("完了した注文はありません。")
        for o in done_orders:
            if o["status"] == "配達完了":
                st.success(f"✅ 番号: {o['id']} (配達完了)")
            elif o["status"] == "配達中":
                st.info(f"🏃 番号: {o['id']} (配達中)")
            elif o["status"] == "配達待ち":
                st.warning(f"📦 番号: {o['id']} (配達係の回収待ち)")

            for item, count in o["items"].items():
                st.write(f" - {item}: {count}個")
            st.divider()

# ==========================================
# 🏃 配達係（デリバリー）画面
# ==========================================
elif mode == "🏃 配達係（デリバリー）":
    st.title("🏃 配達係画面")

    # --- 自動更新の設定 ---
    if st_autorefresh:
        st_autorefresh(interval=5000, key="deliv_refresh")
    else:
        st.warning("⚠️ 自動通知機能を使うには、ターミナルで `pip install streamlit-autorefresh` を実行してください。")

    # --- 調理完了の通知ロジック ---
    current_deliv_state = [o["id"] for o in db["orders"] if o["status"] == "配達待ち"]

    if "known_deliv_state" not in st.session_state:
        st.session_state.known_deliv_state = current_deliv_state.copy()

    for oid in current_deliv_state:
        if oid not in st.session_state.known_deliv_state:
            st.toast(f"📦 調理完了！（番号: {oid}）回収をお願いします。", icon="🏃")

    st.session_state.known_deliv_state = current_deliv_state.copy()

    # --- 画面表示 ---
    if st.button("🔄 最新の状況を手動で確認する", use_container_width=True):
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["📦 配達待ち", "🏃 配達中", "🏁 配達完了履歴"])

    with tab1:
        st.subheader("調理場から受け取るもの")
        wait_orders = sorted([o for o in db["orders"] if o["status"] == "配達待ち"], key=lambda x: x["id"])
        if not wait_orders:
            st.info("現在、配達待ちの注文はありません。")
        for o in wait_orders:
            with st.container(border=True):
                st.markdown(f"## 🧾 番号: {o['id']}")
                for item, count in o["items"].items():
                    st.markdown(f"- {item}： **{count}** 個")
                if st.button(f"🏃‍♂️ 回収して「配達中」にする", key=f"deliv_start_{o['id']}", type="primary", use_container_width=True):
                    o["status"] = "配達中"
                    st.rerun()

    with tab2:
        st.subheader("現在店頭へ運んでいるもの")
        deliv_orders = sorted([o for o in db["orders"] if o["status"] == "配達中"], key=lambda x: x["id"])
        if not deliv_orders:
            st.info("現在、配達中の注文はありません。")
        for o in deliv_orders:
            with st.container(border=True):
                st.markdown(f"## 🧾 番号: {o['id']}")
                if st.button(f"🏁 店頭に渡し「配達完了」にする", key=f"deliv_done_{o['id']}", type="primary", use_container_width=True):
                    o["status"] = "配達完了"
                    st.rerun()

    with tab3:
        done_orders = sorted([o for o in db["orders"] if o["status"] == "配達完了"], key=lambda x: x["id"])
        if not done_orders:
            st.write("配達完了した注文はありません。")
        for o in done_orders:
            with st.expander(f"✅ 番号: {o['id']}"):
                for item, count in o["items"].items():
                    st.write(f"- {item} : {count}個")
