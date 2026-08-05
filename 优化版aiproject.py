import streamlit as st
import os
import json
import hashlib
from datetime import datetime, timezone, timedelta
from openai import OpenAI
from supabase import create_client, Client

# 调时差
tz_bj = timezone(timedelta(hours=8))

# ================= 页面配置 =================
st.set_page_config(
    page_title="我是一个猪能伴侣",
    page_icon="🐷",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ================= supabase =================
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
if "logged_in" not in st.session_state: #是否登录
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
    # =================   =============
if "name" not in st.session_state:
    st.session_state.name = '两脚兽'
if "message" not in st.session_state:
    st.session_state.message = []
if "file" not in st.session_state:
    st.session_state.file = datetime.now(tz_bj).strftime("和小猪在%Y-%m-%d_%H-%M-%S说话了")


# ================= 函数 =================
def save_session_to_db():
    if st.session_state.message:
        data = {
            "username": st.session_state.username,
            "name":st.session_state.name,
            "file": st.session_state.file,
            "message_data": st.session_state.message,
            "updated_at": datetime.now(tz_bj).isoformat()
        }

        # 先删除同名的旧记录
        supabase.table("pig_chats").delete().eq("username", st.session_state.username).eq("file",
                                                                                          st.session_state.file).execute()
        # 插入新记录
        supabase.table("pig_chats").insert(data).execute()


def load_session_from_db(session_name):
    result = supabase.table("pig_chats").select("*").eq("username", st.session_state.username).eq("file",
                                                                                               session_name).execute()
    if result.data:
        st.session_state.message = result.data[0]["message_data"]
        st.session_state.file = session_name


def delete_session_from_db(session_name):
    supabase.table("pig_chats").delete().eq("username", st.session_state.username).eq("file",
                                                                                      session_name).execute()
    if session_name == st.session_state.file:
        st.session_state.message = []
        st.session_state.file = datetime.now(tz_bj).strftime("和小猪在%Y-%m-%d_%H-%M-%S说话了")


# ================= 登录与注册界面 =================
if not st.session_state.logged_in:
    st.title("🐷 欢迎来到小猪伴侣")
    st.markdown("请先登录或注册，你的聊天记录将会被小猪安全地保存哦！")

    tab1, tab2 = st.tabs(["登录", "注册"])
    # =========登录===========================
    with tab1:
        login_user = st.text_input("用户名", key="login_user")
        login_pwd = st.text_input("密码", type="password", key="login_pwd")
        if st.button("登录", type="primary"):
            if login_user and login_pwd:
                result = supabase.table("pig_users").select("*").eq("username", login_user).execute()
                if result.data and result.data[0]["password"] == hash_password(login_pwd):
                    st.session_state.logged_in = True
                    st.session_state.username = login_user

                    st.success("登录成功！")
                    st.rerun()
                else:
                    st.error("用户名或密码错误！")
    #  ================注册=======================
    with tab2:
        reg_user = st.text_input("设置用户名", key="reg_user")
        reg_pwd = st.text_input("设置密码", type="password", key="reg_pwd")
        if st.button("注册账号"):
            if reg_user and reg_pwd:
                # 检查是否已存在
                result = supabase.table("pig_users").select("*").eq("username", reg_user).execute()
                if result.data:
                    st.error("这个名字已经被其他两脚兽占用了！")
                else:  # 往pigchat添加piguser
                    supabase.table("pig_users").insert(
                        {"username": reg_user, "password": hash_password(reg_pwd)}).execute()
                    st.success("注册成功！请切换页面登录")

else:
    # ================= 主界面===============
    st.caption(
        "清晨醒来，我被日历上的数字吓了一跳——现在竟是2036年！更匪夷所思的是，推开窗户，整个世界发生了翻天覆地的变化。枝头的麻雀、邻居的金毛，甚至是动物园里的猛兽，竟然全都变成了一只只圆滚滚、粉嫩嫩的萌系小猪！它们“哼哧哼哧”地迈着小短腿，在街上笨拙地跑来跑去。面对这个被粉红泡泡和可爱猪叫声占领的奇妙世界，我彻底陷入了沉思……",
        width=700)
    st.subheader(f"你想和小猪说说话吗...? ")

    client = OpenAI(api_key=st.secrets['DEEPSEEK_API_KEY'], base_url="https://api.deepseek.com")
    # ================提示词======================
    system_prompt = f"你是一个小猪，但是你非常聪明，和你聊天的是{st.session_state.name}你是人类的好帮手，用可爱的语气回答他的问题，但是不要太长哦"

    # ================= 侧边栏 =================
    with st.sidebar:
        st.header("⏲ 小猪面板")
        if st.button("新建会话", icon="📩", width="stretch"):
            if st.session_state.message:
                st.session_state.message = []
                st.session_state.file = datetime.now(tz_bj).strftime("和小猪在%Y-%m-%d_%H-%M-%S说话了")
                st.session_state.name = '两脚兽'
                st.rerun()

        # ===========历史记录=======
        st.markdown("会话记录：")
        result = supabase.table("pig_chats").select("file").eq("username", st.session_state.username).order(
            "updated_at", desc=True).execute()

        if result.data:
            col1, col2 = st.columns([0.8, 0.2])
            for i, record in enumerate(result.data):
                file_name = record["file"]
                # 截取显示名字，避免太长
                display_name =file_name[4:21]

                with col1:
                    if st.button(display_name, icon="📋", width="stretch", key=f"load_{i}_{file_name}",
                                 type="primary" if file_name == st.session_state.file else "secondary"):
                        load_session_from_db(file_name)
                        st.rerun()
                with col2:
                    if st.button("❌", key=f"del_{i}_{file_name}"):
                        delete_session_from_db(file_name)
                        st.rerun()
        else:
            st.markdown("你还没有和小猪说过话！")

        st.divider()

        st.image("./resource/pig2.jpg", caption="小猪正在思考")
        input_name = st.text_area("你想要小猪叫你什么呢", placeholder="请输入你的昵称", value=st.session_state.name)
        if input_name:
            st.session_state.name = input_name

        if st.button("退出登录", icon="🔚"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.message = []
            st.rerun()

    # ================= 聊天展示区 =================
    st.markdown(f"当前会话: {st.session_state.file}")
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

        save_session_to_db()
        with st.chat_message("assistant", avatar="🐷"):
            with st.spinner("🐷 小猪正在吭哧吭哧地翻找词典..."):
                response = client.chat.completions.create(
                    model="deepseek-v4-pro",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *st.session_state.message  # 解包
                    ],
                    stream=True
                )


            message_response = st.empty()
            full_response = ''
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    message_response.markdown(full_response + "▌")
            message_response.markdown(full_response)

        st.session_state.message.append({"role": "assistant", "content": full_response})

        save_session_to_db()
