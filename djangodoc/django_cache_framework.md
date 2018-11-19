## Django 的缓存框架
> 翻译官: Brian Zhu

动态网站的基本权衡是， 它们是动态的。 每次用户请求一个页面时， Web服务器都会进行各种计算 - 从数据库查询到模板呈现再到业务逻辑 - 以创建站点访问者看到的页面。 从处理开销的角度来看， 这比标准的文件读取文件系统服务器安排要昂贵得多。

对于大多数Web应用程序来说， 这种开销并不是什么大问题。 大多数Web应用程序不是washingtonpost.com或slashdot.org; 他们只是中小型网站， 拥有一般的流量。 但对于中高流量站点， 必须尽可能减少开销。

这就是缓存的用武之地。

缓存某些内容是为了节省昂贵的计算资源， 这样您就不必在下次再执行计算。 这里有一些伪代码解释了对于动态生成的Web页面缓存是如何工作的：

    given a URL, try finding that page in the cache
    if the page is in the cache:
        return the cached page
    else:
        generate the page
        save the generated page in the cache (for next time)
        return the generated page

Django带有一个强大的缓存系统， 可以让您保存动态页面， 这样就不必为每个请求执行计算。 为方便起见， Django提供了不同级别的缓存粒度： 您可以缓存特定视图的输出， 或者只缓存难以生成的部分， 再或者可以缓存整个站点。

Django也可以很好的与“下游”缓存一起工作， 例如Squid和基于浏览器的缓存。 这些是您不用直接控制的缓存类型，但您可以提供有关缓存网站部分的提示（通过HTTP标头）以及如何缓存。

> 参见
> [Cache Framework design philosophy](https://docs.djangoproject.com/en/dev/misc/design-philosophies/#cache-design-philosophy) 解释了框架的一些设计决策。

### 设置缓存

缓存系统需要一些少量的设置。 也就是说， 您必须告诉它缓存数据应该存在哪里 - 无论是在数据库中， 在文件系统中， 还是直接存在内存中。 这是影响缓存性能的重要决策; 现实的情况是， 某些缓存类型确实比其他缓存类型更快。

缓存参数位于settings文件的CACHES设置中。 以下是CACHES所有可用值的说明。

#### Memcached

Memcached是Django本身支持的最快，最有效的缓存类型， 它是一个完全基于内存的缓存服务器， 最初是为了处理LiveJournal.com的高负载而开发的， 后来由Danga Interactive开源。 Facebook和Wikipedia等网站使用它来减少数据库访问并显著提高网站性能。

Memcached作为守护进程运行，并分配了指定数量的内存。 它所做的就是提供一个快速接口，用于在缓存中添加，检索和删除数据。 所有数据都直接存储在内存中， 因此不会产生数据库或文件系统使用的开销。

安装Memcached后，您需要安装Memcached Python绑定。 有几个Python Memcached绑定package可用; 最常见的两个是python-memcached和pylibmc。

在Django中使用Memcached：

- 将 BACKEND 设置为 django.core.cache.backends.memcached.MemcachedCache 或者 django.core.cache.backends.memcached.PyLibMCCache (取决于您选择的memcached绑定)

- 将 LOCATION 设置为 ip:port 的值, 其中的ip是Memcached守护程序的IP地址， port是运行Memcached的端口，或者是 unix：path 的值， 其中的path是Memcached Unix socket 文件的路径。

在下面的示例中， Memcached使用python-memcached绑定在地址为localhost（127.0.0.1）， 端口为11211的Memcached服务器：

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
        }
    }

在下面的示例中， Memcached可通过本地Unix socket 文件/tmp/memcached.sock使用python-memcached绑定获得：

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': 'unix:/tmp/memcached.sock',
        }
    }

当使用pylibmc绑定时， 请不要包含 unix：/ 前缀：

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
            'LOCATION': '/tmp/memcached.sock',
        }
    }

Memcached的一个出色功能是它能够在多个服务器上共享缓存。 这意味着您可以在多台计算机上运行Memcached守护程序， 程序会将该组服务器视为单个缓存， 而无需在每台计算机上复制缓存值。 要利用这个功能， 请在 LOCATION 中包含所有服务器地址， 可以是分号或逗号分隔的字符串， 也可以是列表。

在下面的示例中， 缓存通过端口为11211， IP地址为172.19.26.240和172.19.26.242上运行的Memcached实例来实现共享：

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': [
                '172.19.26.240:11211',
                '172.19.26.242:11211',
            ]
        }
    }

在下面的示例中， 缓存通过在IP地址为172.19.26.240（端口11211）， 172.19.26.242（端口11212）和172.19.26.244（端口11213）上运行的Memcached实例来实现共享：

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': [
                '172.19.26.240:11211',
                '172.19.26.242:11212',
                '172.19.26.244:11213',
            ]
        }
    }

关于Memcached的一个关键问题是， 基于内存的缓存有一个缺点： 因为缓存的数据存储在内存中， 如果服务器崩溃了， 数据将会丢失。 显然， 内存不适用于永久数据存储， 因此不要依赖基于内存的缓存作为唯一的数据存储。 毫无疑问， 没有任何关于Django缓存的后端应该用于永久存储 - 它们都是用于缓存数据而不是存储的解决方案 - 但我们在此指出这一点， 是因为基于内存的缓存是暂时的。

-------------

#### Database caching

Django可以将其缓存的数据存储在数据库中。 如果你有一个快速， 索引良好的数据库服务器， 这种方法效果最好。

将数据库表用作缓存后端：

- 将 BACKEND 设置为 django.core.cache.backends.db.DatabaseCache

- 将 LOCATION 设置为 tablename， 即数据库表的名称。 此名称可以是您想要的任何名称， 只要它是一个尚未在您的数据库中使用的有效表名。

在下面的示例中， 缓存表的名称为my_cache_table：

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'my_cache_table',
        }
    }

##### Creating the cache table

在使用数据库缓存之前， 必须使用以下命令创建缓存表：

    python manage.py createcachetable

这会在数据库中创建一个表， 该表的格式与Django的数据库缓存系统所期望的格式相同。 该表的名称取自 LOCATION。

如果您在使用多个数据库缓存， createcachetable 会为每个缓存创建一个表。

如果您在使用多个数据库， createcachetable 将遵循数据库路由器的 allow_migrate（） 方法（请参见下文）。

与 migrate 一样， createcachetable 也不会触及现有表。 它只会创建缺少的表。

想要打印要运行的SQL， 而不是执行它， 请使用 createcachetable --dry-run 选项。

-------------

##### Multiple databases

如果对多个数据库使用数据库缓存，则还需要为数据库缓存表设置路由指令。
出于路由的目的，数据库缓存表在名为django_cache的应用程序中显示为名为CacheEntry的模型。
此模型不会出现在模型缓存中，但模型详细信息可用于路由目的。
例如，以下路由器将所有缓存读取操作定向到cache_replica，并将所有写入操作定向到cache_primary。
缓存表只会同步到cache_primary：

    class CacheRouter:
        """A router to control all database cache operations"""
    
        def db_for_read(self, model, **hints):
            "All cache read operations go to the replica"
            if model._meta.app_label == 'django_cache':
                return 'cache_replica'
            return None
    
        def db_for_write(self, model, **hints):
            "All cache write operations go to primary"
            if model._meta.app_label == 'django_cache':
                return 'cache_primary'
            return None
    
        def allow_migrate(self, db, app_label, model_name=None, **hints):
            "Only install the cache model on primary"
            if app_label == 'django_cache':
                return db == 'cache_primary'
            return None

如果未指定数据库缓存模型的路由方向，则缓存后端将使用默认数据库。
当然，如果不使用数据库缓存后端，则无需担心为数据库缓存模型提供路由指令。

-------------

##### Filesystem caching

基于文件的后端将每个缓存值序列化并存储为单独的文件。 要使用此后端， 请将 BACKEND 设置为 “django.core.cache.backends.filebased.FileBasedCache”， 并将 LOCATION 设置为合适的目录。 例如， 要将缓存数据存储在 /var/tmp/django_cache 中， 请使用以下设置：

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': '/var/tmp/django_cache',
        }
    }

如果您使用的是Windows， 请将驱动器号放在路径的开头， 如下所示：

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': 'c:/foo/bar',
        }
    }

目录应该是绝对路径 - 也就是说， 它应该从文件系统的根目录开始。 是否在设置的末尾添加斜杠并不重要。

确保此设置指向的目录存在， 并且由运行时Web服务器的系统用户可读写。 继续上面的示例， 如果您的服务器以用户 apache 运行，请确保目录 /var/tmp/django_cache 存在且用户 apache 可读写。

-------------

##### Local-memory caching

如果未在设置文件中指定其他缓存， 那么这个就是默认缓存。 如果您想要内存缓存的速度优势但不具备运行Memcached的能力， 请考虑使用本地内存缓存后端。 此缓存是按进程（见下文）和线程安全的。 要使用它， 请将 BACKEND 设置为 “django.core.cache.backends.locmem.LocMemCache”。 例如：

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }

缓存 LOCATION 用于标识各个内存存储。 如果您只有一个 locmem 缓存， 则可以省略 LOCATION; 但是， 如果您有多个本地内存缓存， 则需要为其中至少一个分配一个名称， 以便将它们分开。

缓存使用最近最少使用（LRU）的剔除策略。

请注意， 每个进程都有自己的私有缓存实例， 这意味着不可能进行跨进程缓存。 这显然也意味着本地内存缓存不是特别节省内存， 因此它可能不是生产环境的一个好的选择。 但对开发很有好处。

> **在 Django 2.1 中的更改:**
> 旧版本使用伪随机剔除策略而不是LRU。

-------------

##### Dummy caching (for development)

最后， Django 带有一个“虚拟”缓存， 实际上并不缓存 - 它只是实现缓存接口而不做任何事情。

如果您的生产站点在不同的地方使用重型缓存， 但在开发/测试环境中您不想使用缓存并且不希望将代码更改为特殊情况（后者）， 这将非常有用。 要激活虚拟缓存， 请将 BACKEND 设置为：

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

-------------

##### Using a custom cache backend

虽然Django支持开箱即用的许多缓存后端， 但有时您可能希望使用自定义的缓存后端。 要在Django中使用外部缓存后端， 请使用Python导入路径作为 CACHES 设置的 BACKEND， 如下所示：

    CACHES = {
        'default': {
            'BACKEND': 'path.to.backend',
        }
    }

如果您正在构建自己的后端， 则可以使用标准缓存后端作为参考实现。 您将在Django源代码的 django/core/cache/backends/ 目录中找到代码。
注意： 如果没有真正令人信服的理由， 例如不支持它们的主机， 您应该坚持使用Django附带的缓存后端。 它们经过了良好的测试， 并且易于使用。

-------------

##### Cache arguments

可以为每个缓存后端提供额外的参数来控制缓存行为。 这些参数作为 CACHES 设置中的附加键提供。 有效参数如下：

+ TIMEOUT： 用于缓存的默认超时（以秒为单位）。 此参数默认为300秒（5分钟）。 您可以将 TIMEOUT 设置为 None， 以便默认情况下缓存键永不过期。 值设为0会导致密钥立即过期（实际上就是“不缓存”）。

+ OPTIONS： 需要传递给缓存后端的任何选项。 有效选项列表将随每个后端而变化， 由第三方库支持的缓存后端将直接将其选项传递给底层缓存库。

缓存后端需要实现自己的剔除策略（即locmem， filesystem 和 database 后端）将遵循以下选项：

- 
  - MAX_ENTRIES： 删除旧值之前缓存中允许的最大条目数。 此参数默认为300。
  
  - CULL_FREQUENCY： 达到 MAX_ENTRIES 时剔除的条目部分。 实际比率为 1 / CULL_FREQUENCY， 因此将 CULL_FREQUENCY 设置为2可在达到 MAX_ENTRIES 时剔除一半条目。 此参数应为整数， 默认为3。

 CULL_FREQUENCY 的值为0意味着在达到 MAX_ENTRIES 时将转储整个缓存。 在一些后端（特别是数据库）上， 这使得剔除速度更快， 但代价是更多的缓存未命中。
 
Memcached后端将 OPTIONS 的内容作为关键字参数传递给客户端构造函数， 从而允许对客户端行为进行更高级的控制。 例如， 请参见下文。

+ KEY_PREFIX： 一个字符串， 将自动被包含（默认情况下预先添加）到Django服务器使用的所有缓存键。

+ VERSION： Django服务器生成的缓存键的默认版本号。

+ KEY_FUNCTION： 包含函数的虚线路径的字符串， 该函数定义如何将前缀， 版本和密钥组合为最终缓存密钥。 (A string containing a dotted path to a function that defines how to compose a prefix, version and key into a final cache key.)

 有关更多信息，请参阅缓存文档[cache documentation](https://docs.djangoproject.com/en/2.1/topics/cache/#cache-key-prefixing)。

在下面的示例中， 正在配置一个文件系统作为后端， 超时时间为60秒， 最大容量为1000个项目的缓存：

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': '/var/tmp/django_cache',
            'TIMEOUT': 60,
            'OPTIONS': {
                'MAX_ENTRIES': 1000
            }
        }
    }

以下是基于python-memcached的后端的示例配置， 对象大小限制为2MB：

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
            'OPTIONS': {
                'server_max_value_length': 1024 * 1024 * 2,
            }
        }
    }

以下是基于pylibmc的后端的示例配置， 该后端支持二进制协议， SASL 身份验证和 ketama 行为模式：

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
            'LOCATION': '127.0.0.1:11211',
            'OPTIONS': {
                'binary': True,
                'username': 'user',
                'password': 'pass',
                'behaviors': {
                    'ketama': True,
                }
            }
        }
    }

-------------

##### The per-site cache

设置缓存后， 使用缓存的最简单方法是缓存整个站点。 您需要将 “django.middleware.cache.UpdateCacheMiddleware” 和 “django.middleware.cache.FetchFromCacheMiddleware” 添加到 MIDDLEWARE 设置中， 如下例所示：

    MIDDLEWARE = [
        'django.middleware.cache.UpdateCacheMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.cache.FetchFromCacheMiddleware',
    ]

> 注意
> 不， 这不是一个错字： "update" 中间件必须是列表中的第一个， "fetch" 中间件必须是最后一个。 细节有点模糊， 但如果你想要知道完整的故事，请参阅下面的 [Order of MIDDLEWARE](https://docs.djangoproject.com/en/2.1/topics/cache/#order-of-middleware)。

然后， 将以下必选项添加到Django设置文件中：

- CACHE_MIDDLEWARE_ALIAS - 用于存储的缓存别名。

- CACHE_MIDDLEWARE_SECONDS - 每个页面应缓存的秒数。

- CACHE_MIDDLEWARE_KEY_PREFIX - 如果使用相同的Django安装包在多个站点之间共享缓存， 请将其设置为站点名称或此Django实例特有的其他字符串， 以防止发生密钥冲突。 如果你不在乎，请使用空字符串。

FetchFromCacheMiddleware 缓存状态为200的GET和HEAD响应， 在请求和响应头允许的情况下。 对具有不同查询参数的相同URL的请求的响应被认为是唯一页面并且会被单独缓存。 该中间件期望使用与相应的GET请求相同的响应头来回答HEAD请求; 在这种情况下， 它可以返回HEAD请求的缓存GET响应。 (FetchFromCacheMiddleware caches GET and HEAD responses with status 200, where the request and response headers allow. Responses to requests for the same URL with different query parameters are considered to be unique pages and are cached separately. This middleware expects that a HEAD request is answered with the same response headers as the corresponding GET request; in which case it can return a cached GET response for HEAD request.)

此外， UpdateCacheMiddleware 会在每个 HttpResponse 中自动设置几个头部：

- 将 Expires 头部设置为当前日期/时间加上定义的 CACHE_MIDDLEWARE_SECONDS。

- 设置 Cache-Control 头部来给出页面的存活时间 - 同样， 从 CACHE_MIDDLEWARE_SECONDS 设置。

有关中间件的更多信息， 请参阅中间件[Middleware](https://docs.djangoproject.com/en/2.1/topics/http/middleware/)。

如果视图设置了自己的缓存到期时间（即它的 Cache-Control 头部中有 max-age 部分）， 那么页面将被缓存直到到期时间， 而不是 CACHE_MIDDLEWARE_SECONDS。 使用 django.views.decorators.cache 中的装饰器， 您可以轻松设置视图的到期时间（使用 cache_control（） 装饰器）或禁用视图的缓存（使用 never_cache（） 装饰器）。 有关这些装饰器的更多信息，请参阅 [using other headers](https://docs.djangoproject.com/en/2.1/topics/cache/#controlling-cache-using-other-headers) 部分。

如果 USE_I18N 被设置为 True， 则生成的缓存键将包含活动语言 [language](https://docs.djangoproject.com/en/2.1/topics/i18n/#term-language-code) 的名称 - 另请参阅 [How Django discovers language preference](https://docs.djangoproject.com/en/2.1/topics/i18n/translation/#how-django-discovers-language-preference) 。 这使您可以轻松缓存多语言网站， 而无需自己创建缓存密钥。

当 USE_L10N 设置为 True 时， 缓存键还包括活动语言 [language](https://docs.djangoproject.com/en/2.1/topics/i18n/#term-language-code) ， 当 USE_TZ 设置为 True 时， 缓存键还包括当前时区 [current time zone](https://docs.djangoproject.com/en/2.1/topics/i18n/timezones/#default-current-time-zone) 。

-------------

##### The per-view cache

**django.views.decorators.cache.cache_page()**

使用缓存框架的更精细方法是缓存单个视图的输出。 django.views.decorators.cache 定义了一个 cache_page 装饰器， 它将自动缓存视图的响应。 它非常易于使用：

    from django.views.decorators.cache import cache_page
    
    @cache_page(60 * 15)
    def my_view(request):
        ...

cache_page 采用单个参数： 缓存超时时间， 以秒为单位。 在上面的示例中， my_view（） 视图的结果将缓存15分钟。 （请注意，为了便于阅读，我们将其写为 60 * 15。 60 * 15 将被评估为900 - 即15分钟乘以每分钟60秒。）

每个视图缓存， 像每个站点的缓存一样， 都是从URL键入的。 如果多个URL指向同一视图， 则每个URL将单独缓存。 继续 my_view 示例， 如果您的URLconf如下所示：

    urlpatterns = [
        path('foo/<int:code>/', my_view),
    ]

那么对 /foo/1/ 和 /foo/23/ 的请求将被单独缓存， 正如您所期望的那样。 但是一旦请求了特定的URL（例如， /foo/23/ ）， 对该URL的后续请求将使用该缓存。

cache_page 还可以使用一个可选的关键字参数 cache， 它指示装饰器在缓存视图结果时使用特定的缓存（来自您的 CACHES 设置）。 默认情况下， 将使用默认缓存， 但您可以指定想要的任何缓存：

    @cache_page(60 * 15, cache="special_cache")
    def my_view(request):
        ...

您还可以基于每个视图覆盖缓存前缀。 cache_page 采用可选的关键字参数 key_prefix， 其作用方式与中间件的 CACHE_MIDDLEWARE_KEY_PREFIX 设置相同。 它可以像这样使用：

    @cache_page(60 * 15, key_prefix="site1")
    def my_view(request):
        ...

key_prefix 和 cache 参数可以一起指定。 将连接 key_prefix 参数和 CACHES 下指定的 KEY_PREFIX。

##### Specifying per-view cache in the URLconf



















































































