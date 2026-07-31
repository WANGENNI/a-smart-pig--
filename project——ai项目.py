import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import json

# ================= 页面基本配置 =================
print("---------->重新加载页面\n")
st.set_page_config(
    page_title="我是一个猪能伴侣",
    page_icon="🐷",
    # 布局 wide/centred
    layout="wide",
    # 侧边栏
    initial_sidebar_state="expanded",
    # 菜单
    menu_items={
        'About': "# 这是一个猪"
    }
)
# 标题
st.caption("清晨醒来，我被日历上的数字吓了一跳——现在竟是2036年！更匪夷所思的是，推开窗户，整个世界发生了翻天覆地的变化。枝头的麻雀、邻居的金毛，甚至是动物园里的猛兽，竟然全都变成了一只只圆滚滚、粉嫩嫩的萌系小猪！它们“哼哧哼哧”地迈着小短腿，在街上笨拙地跑来跑去。面对这个被粉红泡泡和可爱猪叫声占领的奇妙世界，我彻底陷入了沉思……",width=700)
st.header("你想和小猪说说话吗...?",width=500)
# logo
st.logo("./resource/pig.jpg",size="large")


#==================  保存会话函数=======================
def save_session():
    if st.session_state.file:  # (如果会话名字存在的话)
        data = {
            "file": st.session_state.file,
            "name": st.session_state.name,
            "message": st.session_state.message
        }
        if not os.path.exists("会话记录"):  # 判断路径是否存在
            os.makedirs("会话记录")# 创建文件夹

        # 写入数据
        with open(f"会话记录/{st.session_state.file}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)  # 把data写入f，不要转义显示中文，缩进2格


# ================== 初始化=====================

# 创建保存用户昵称
if "name" not in st.session_state:
    st.session_state.name = '两脚兽'


# 创建保存聊天记录列表
if "message" not in st.session_state:
    st.session_state.message = []

# 创建保存会话文件
if "file" not in st.session_state:
    st.session_state.file = datetime.now().strftime("和小猪在%Y-%m-%d_%H-%M-%S说话了")


# ============================================侧边栏====================================================
with st.sidebar:
    st.header("⏲小猪面板")
    st.markdown("\n")

    # =============按下按钮===============
    if st.button("新建会话", help="按这个可以新建和小猪的对话", icon="📩", icon_position="right", width="stretch"):
        if st.session_state.message:  # message有内容True
            # 新建会话，初始化上次会话内容
            st.session_state.message = []
            st.session_state.name = '两脚兽'
            st.session_state.file = datetime.now().strftime("和小猪在%Y-%m-%d_%H-%M-%S说话了")  # 新建文件


    # 加载会话列表

    if os.path.exists("会话记录"):  #文件夹路径存在
        if os.listdir("会话记录")!=[]:
            st.markdown("你之前和小猪的对话：")
            file_list = os.listdir("会话记录")
            col1, col2 = st.columns([0.8, 0.2])
            i=0
            for file in file_list:
                if file.endswith(".json"): # 以json结尾的
                    file = file[4:22]
                    with col1:
                        st.button(f"{file}",icon="📋",width="stretch",key=f"history_btn_{i}_{file}")
                    with col2:
                        st.button("❌",key=f"delete_btn_{i}_{file}")
                i=i+1

        else:
            st.markdown("你还没有和小猪说过话！")
            st.markdown("快去和他聊聊吧")
    else:
        st.markdown("你还没有和小猪说过话！")
        st.markdown("快去和他聊聊吧")



    st.markdown("\n")
    st.image("./resource/pig2.jpg",caption="小猪正在思考")
    input_name = st.text_area("你想要小猪叫你什么呢",placeholder="请输入你的昵称",value=st.session_state.name)
    if input_name:
        st.session_state.name = input_name



# =========================================系统提示词==========================================
system_prompt = f"你是一个小猪，但是你非常聪明，和你聊天的是{st.session_state.name}你是人类的好帮手，用可爱的语气回答他的问题，但是不要太长哦"




# 创建ai大模型
client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'),base_url="https://api.deepseek.com")


# 展示聊天记录
for message in st.session_state.message:
    if message["role"] == "user":
        st.chat_message("user",avatar="🐶").write(f"{message['content']}")
    else:
        st.chat_message("assistant",avatar="🐷").write(f"{message['content']}")



# =====================================输入===============================
prompt = st.chat_input("say something")

if prompt:# 字符串非空  ——>True
    st.chat_message("user",avatar="🐶").write(f"{prompt}")

    st.session_state.message.append({"role": "user", "content": prompt})

    # 调用ai
    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            # 系统提示词
            {"role": "system", "content": system_prompt},
            # 滚雪球 记忆对话   # {"role": "user", "content": prompt},{"role": "assistant", "content":,
            *st.session_state.message  # 把massage（dict）的内容解包出

        ],
        stream=True,
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}}
    )
    # stream = False
    # st.chat_message("assistant",avatar="🐷").write(response.choices[0].message.content)
    # print("<-------------ai返回结果：",response.choices[0].message.content,"\n")
    # st.session_state.message.append({"role": "assistant", "content": response.choices[0].message.content})

    with st.chat_message("assistant", avatar="🐷"):
        # 占位
        message_response = st.empty()
        full_response = ''

        # 循环接收流式数据
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content

                message_response.markdown(full_response + "▌",help="小猪的猪脑正在疯狂思考中...")

        message_response.markdown(full_response,help="小猪思考完成！")

    st.session_state.message.append({"role": "assistant", "content": full_response})
    save_session()