import streamlit as st
import os
from openai import OpenAI

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

if "name" not in st.session_state:
    st.session_state.name = '两脚兽'


# 系统提示词
system_prompt = f"你是一个小猪，但是你非常聪明，和你聊天的是{st.session_state.name}你是人类的好帮手，用可爱的语气回答他的问题，但是不要太长哦"

# 侧边栏
with st.sidebar:
    st.header("侧边栏")
    input_name = st.text_area("你想要小猪叫你什么呢",placeholder="请输入你的昵称",value="两脚人类")
    if input_name:
        st.session_state.name = input_name

client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'),base_url="https://api.deepseek.com")


# 创建保存聊天列表
if "message" not in st.session_state:
    st.session_state.message = []

# 展示聊天记录
for message in st.session_state.message:
    if message["role"] == "user":
        st.chat_message("user",avatar="🐶").write(f"{message['content']}")
    else:
        st.chat_message("assistant",avatar="🐷").write(f"{message['content']}")




# 输入框
prompt = st.chat_input("say something")

if prompt:# 字符串非空  ——>True
    st.chat_message("user",avatar="🐶").write(f"{prompt}")
    print("--------->调用ai大模型，提示词：",prompt,"\n")

    st.session_state.message.append({"role": "user", "content": prompt})
#
    print([
            # 系统提示词
            {"role": "system", "content": system_prompt},
            # 滚雪球 记忆对话   # {"role": "user", "content": prompt},
            *st.session_state.message  # 把massage（dict）的内容解包出

        ])
#
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

    # stream = True
    # response_message = st.empty()  # 创建一个空对象
    # full_response = ''
    # for chunk in response:
    #     if chunk.choices[0].delta.content is not None:
    #         content = chunk.choices[0].delta.content
    #         full_response += content
    #         response_message.chat_message("assistant",avatar="🐷").write(full_response)
    #
    # st.session_state.message.append({"role": "assistant", "content": full_response})
    # 1. 先固定好外层的聊天气泡和头像
    with st.chat_message("assistant", avatar="🐷"):

        # 2. 在气泡“内部”挖一个坑，用来动态更新文字
        message_response = st.empty()
        full_response = ''

        # 3. 循环接收流式数据
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content

                # 4. 只刷新坑里的 Markdown 文本，加上一个光标(▌)显得更像在打字
                message_response.markdown(full_response + "▌",help="小猪的猪脑正在疯狂思考中...")

        # 5. 循环结束后，把光标去掉，显示最终文本
        message_response.markdown(full_response,help="小猪思考完成！")

    # 6. 保存到历史记录中
    st.session_state.message.append({"role": "assistant", "content": full_response})