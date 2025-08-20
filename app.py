import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from collections import deque
import datetime

import pyvisa

# --- 初始化TC290 ---
rm = pyvisa.ResourceManager()

TC290 = rm.open_resource("ASRL3::INSTR")
TC290.baud_rate = 115200
TC290.query('*IDN?')

def get_temperature():
    KRDG = TC290.query("KRDG? A")
    tmp = float(KRDG.strip())
    temperature = f"{tmp:.4f}"
    return temperature


# --- 初始化Dash应用 ---
app = dash.Dash(__name__)

# --- 数据存储 ---
# 使用deque可以高效地在列表两端添加或删除元素
# 这里我们设定图表最多只显示100个数据点
MAX_DATA_POINTS = 100
X_values = deque(maxlen=MAX_DATA_POINTS)
Y_values = deque(maxlen=MAX_DATA_POINTS)

# 初始数据
X_values.append(datetime.datetime.now())
Y_values.append(get_temperature())


# --- 应用布局 (Layout) ---
app.layout = html.Div([
    html.H1("Dash 实时监控图表"),
    
    # 图表组件，用于显示我们的实时数据
    dcc.Graph(id='live-update-graph'),
    
    # 核心组件：Interval计时器
    # 它会每1000毫秒（1秒）触发一次id='interval-component'的回调
    dcc.Interval(
        id='interval-component',
        interval=1 * 1000,  # in milliseconds
        n_intervals=0
    )
])


# --- 回调函数 (Callback) ---
# 这个回调函数将 dcc.Interval 的触发与 dcc.Graph 的更新连接起来
@app.callback(
    Output('live-update-graph', 'figure'),  # 输出：更新图表的figure属性
    [Input('interval-component', 'n_intervals')] # 输入：监听计时器的触发事件
)
def update_graph_live(n):
    # n_intervals 是一个从0开始计数的整数，代表计时器触发了多少次
    # 我们可以用它来决定是否更新数据，或者直接在函数里获取新数据
    
    # 模拟生成新的实时数据
    current_time = datetime.datetime.now()
    new_y_value = get_temperature()
    
    # 更新我们的数据队列
    X_values.append(current_time)
    Y_values.append(new_y_value)
    
    # 创建图表对象
    fig = go.Figure(
        data=[go.Scatter(
            x=list(X_values),
            y=list(Y_values),
            mode='lines+markers',
            name='实时数据'
        )],
        layout=go.Layout(
            title='实时温度监控',
            xaxis=dict(title='时间'),
            yaxis=dict(title='温度 (K)', range=[295, 301]), # 固定Y轴范围
            showlegend=True
        )
    )
    
    return fig

# --- 启动应用 ---
if __name__ == '__main__':
    app.run(debug=True)