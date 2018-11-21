## Django 的 sessions 
> ### [How to use sessions](https://docs.djangoproject.com/en/2.1/topics/http/sessions/)
> 翻译官: Brian Zhu

Django为匿名会话提供全面支持。 会话框架允许您基于每个站点访问者存储和检索任意数据。 它在服务器端存储数据并抽象 cookies 的发送和接收。 Cookies 包含会话ID - 而不是数据本身(除非您使用基于cookie的后端 [cookie based backend](https://docs.djangoproject.com/en/2.1/topics/http/sessions/#cookie-session-backend) )。

### Enabling sessions

