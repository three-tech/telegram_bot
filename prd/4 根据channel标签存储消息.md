根据channel标签存储消息 

1.阅读[database.py](../src/database.py)，为telegram_bot_message表新增一列tag
2.接收转发的channel消息时，如果channelId存在于channel_tag表中，则按原逻辑保存消息，并且保存tag信息
3.接收转发消息时，如果channelId不存在于channel_tag表中，则提示客户端是否新建channel_tag，如果是，则提示选择tag，最后保存channel_tag；如果否，则不做任何处理

强制要求要求：
1. 使用python12的语法规则，使用conda环境telegram_bot环境
2. 严格遵循本需求文档的要求，禁止添加额外的功能
3. 严格遵循[AGENTS.md](../AGENTS.md)的要求
4. 先阐述行动计划，得到明确的批准后才可以动代码
5. 禁止返回模拟数据，禁止写mock数据，代码中不允许出现todo
