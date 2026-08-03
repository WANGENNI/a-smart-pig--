import streamlit as st
import os
import json
import hashlib
from datetime import datetime
from openai import OpenAI
from supabase import create_client, Client

# ================= 页面基本配置 =================
st.set_page_config(
    page_title="我是一个猪能伴侣",
    page_icon="🐷",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ================= 初始化数据库连接 =================
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


supabase: Client = init_supabase()


# ================= 密码加密函数 =================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ================= 初始化 Session State =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "name" not in st.session_state:
    st.session_state.name = '两脚兽'
if "message" not in st.session_state:
    st.session_state.message = []
if "file" not in st.session_state:
    st.session_state.file = datetime.now().strftime("和小猪在%Y-%m-%d_%H-%M-%S说话了")


# ================= 数据库交互函数 =================
def save_session_to_db():
    if st.session_state.message:
        data = {
            "username": st.session_state.username,
            "session_name": st.session_state.file,
            "message_data": st.session_state.message,
            "updated_at": datetime.now().isoformat()
        }
        # 尝试更新，如果不存在则插入 (基于 username 和 session_name，这里为了简单直接覆盖插入同名会话)
        # 先删除同名的旧记录
        supabase.table("pig_chats").delete().eq("username", st.session_state.username).eq("session_name",
                                                                                          st.session_state.file).execute()
        # 插入新记录
        supabase.table("pig_chats").insert(data).execute()


def load_session_from_db(session_name):
    res = supabase.table("pig_chats").select("*").eq("username", st.session_state.username).eq("session_name",
                                                                                               session_name).execute()
    if res.data:
        st.session_state.message = res.data[0]["message_data"]
        st.session_state.file = session_name


def delete_session_from_db(session_name):
    supabase.table("pig_chats").delete().eq("username", st.session_state.username).eq("session_name",
                                                                                      session_name).execute()
    if session_name == st.session_state.file:
        st.session_state.message = []
        st.session_state.file = datetime.now().strftime("和小猪在%Y-%m-%d_%H-%M-%S说话了")


# ================= 登录与注册界面 =================
if not st.session_state.logged_in:
    st.title("🐷 欢迎来到小猪伴侣")
    st.markdown("请先登录或注册，你的聊天记录将会被安全地保存在云端哦！")

    tab1, tab2 = st.tabs(["登录", "注册"])

    with tab1:
        login_user = st.text_input("用户名", key="login_user")
        login_pwd = st.text_input("密码", type="password", key="login_pwd")
        if st.button("登录", type="primary"):
            if login_user and login_pwd:
                res = supabase.table("pig_users").select("*").eq("username", login_user).execute()
                if res.data and res.data[0]["password"] == hash_password(login_pwd):
                    st.session_state.logged_in = True
                    st.session_state.username = login_user
                    st.success("登录成功！")
                    st.rerun()
                else:
                    st.error("用户名或密码错误！")

    with tab2:
        reg_user = st.text_input("设置用户名", key="reg_user")
        reg_pwd = st.text_input("设置密码", type="password", key="reg_pwd")
        if st.button("注册账号"):
            if reg_user and reg_pwd:
                # 检查是否已存在
                check = supabase.table("pig_users").select("*").eq("username", reg_user).execute()
                if check.data:
                    st.error("这个名字已经被其他两脚兽占用了！")
                else:
                    supabase.table("pig_users").insert(
                        {"username": reg_user, "password": hash_password(reg_pwd)}).execute()
                    st.success("注册成功！请切换到登录页面登录。")

else:
    # ================= 主界面 (已登录) =================
    st.caption(
        "清晨醒来，我被日历上的数字吓了一跳——现在竟是2036年！更匪夷所思的是，推开窗户，整个世界发生了翻天覆地的变化。枝头的麻雀、邻居的金毛，甚至是动物园里的猛兽，竟然全都变成了一只只圆滚滚、粉嫩嫩的萌系小猪！它们“哼哧哼哧”地迈着小短腿，在街上笨拙地跑来跑去。面对这个被粉红泡泡和可爱猪叫声占领的奇妙世界，我彻底陷入了沉思……",
        width=700)
    st.header(f"你想和小猪说说话吗...? (当前登录: {st.session_state.username})")

    # AI 客户端配置
    client = OpenAI(api_key=st.secrets['DEEPSEEK_API_KEY'], base_url="https://api.deepseek.com")
    system_prompt = f"你是一个小猪，但是你非常聪明，和你聊天的是{st.session_state.name}你是人类的好帮手，用可爱的语气回答他的问题，但是不要太长哦"

    # ================= 侧边栏 =================
    with st.sidebar:
        st.header("⏲ 小猪面板")
        if st.button("退出登录"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.message = []
            st.rerun()

        st.markdown("\n")
        if st.button("新建会话", icon="📩", width="stretch"):
            if st.session_state.message:
                st.session_state.message = []
                st.session_state.file = datetime.now().strftime("和小猪在%Y-%m-%d_%H-%M-%S说话了")
                st.rerun()

        # 从数据库加载历史记录
        st.markdown("### 📚 你的云端聊天记录：")
        res = supabase.table("pig_chats").select("session_name").eq("username", st.session_state.username).order(
            "updated_at", desc=True).execute()

        if res.data:
            col1, col2 = st.columns([0.8, 0.2])
            for i, record in enumerate(res.data):
                s_name = record["session_name"]
                # 截取显示名字，避免太长
                display_name = s_name[4:23] if len(s_name) > 23 else s_name

                with col1:
                    if st.button(display_name, icon="📋", width="stretch", key=f"load_{i}_{s_name}",
                                 type="primary" if s_name == st.session_state.file else "secondary"):
                        load_session_from_db(s_name)
                        st.rerun()
                with col2:
                    if st.button("❌", key=f"del_{i}_{s_name}"):
                        delete_session_from_db(s_name)
                        st.rerun()
        else:
            st.markdown("你还没有和小猪说过话！")

        st.divider()
        st.image("./resource/pig2.jpg", caption="小猪正在思考")
        input_name = st.text_area("你想要小猪叫你什么呢", placeholder="请输入你的昵称", value=st.session_state.name)
        if input_name:
            st.session_state.name = input_name

    # ================= 聊天展示区 =================
    st.markdown(f"**当前会话:** {st.session_state.file}")
    for message in st.session_state.message:
        if message["role"] == "user":
            st.chat_message("user", avatar="🐶").write(message['content'])
        else:
            st.chat_message("assistant", avatar="🐷").write(message['content'])

    # ================= 输入与 AI 回复 =================
    prompt = st.chat_input("和小猪说点什么吧...")
    if prompt:
        st.chat_message("user", avatar="🐶").write(prompt)
        st.session_state.message.append({"role": "user", "content": prompt})

        # 实时保存一下用户的提问到数据库
        save_session_to_db()

        response = client.chat.completions.create(
            model="deepseek-chat",  # 这里改成你实际可用的 deepseek 模型名
            messages=[{"role": "system", "content": system_prompt}, *st.session_state.message],
            stream=True
        )

        with st.chat_message("assistant", avatar="🐷"):
            message_response = st.empty()
            full_response = ''
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    message_response.markdown(full_response + "▌")
            message_response.markdown(full_response)

        st.session_state.message.append({"role": "assistant", "content": full_response})
        # AI回答完再次保存到数据库
        save_session_to_db()