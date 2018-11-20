## Django 的缓存框架 [Django’s cache framework](https://docs.djangoproject.com/en/2.1/topics/cache/)
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

上一节中的示例硬编码了视图被缓存的事实， 因为 cache_page 改变了 my_view 函数。 这种方法将您的视图耦合到缓存系统， 由于多种原因， 这种方法并不理想。 例如， 您可能希望在另一个无缓存站点上重用此视图函数， 或者您可能希望将视图分发给可能希望在不缓存的情况下使用它们的人员。 这些问题的解决方案是在 URLconf 中指定每个视图的缓存， 而不是用视图函数旁边的装饰器。

这样做很简单： 只需在 URLconf 中引用视图函数和 cache_page 即可。 这是以前的旧URLconf：

    urlpatterns = [
        path('foo/<int:code>/', my_view),
    ]

下面是一样的， my_view 包含在 cache_page 中：

    from django.views.decorators.cache import cache_page
    
    urlpatterns = [
        path('foo/<int:code>/', cache_page(60 * 15)(my_view)),
    ]

-------------

##### Template fragment caching

如果您需要更多控制， 还可以使用缓存模板标记来缓存模板片段。 要让您的模板能够访问此标记， 请将 {% load cache %} 放在模板顶部附近。

(% cache %} 模板标记在给定的时间内缓存块的内容。 它至少需要两个参数： 缓存超时时间（以秒为单位）和提供缓存片段的名称。 如果timeout为 None， 则片段将永久缓存。 名称将按原样使用， 不要使用变量。 例如：

    {% load cache %}
    {% cache 500 sidebar %}
        .. sidebar ..
    {% endcache %}

> 在Django 2.0中更改：
> 旧版本不允许超时设置为 None。

有时， 您可能希望根据片段内显示的某些动态数据缓存片段的多个副本。 例如， 对于站点的每个用户， 您可能需要上一个示例中使用的侧栏的单独缓存副本。 通过将一个或多个其他参数（可能是带或不带过滤器的变量）传递给 {% cache %} 模板标记来唯一标识缓存片段来执行此操作：

    {% load cache %}
    {% cache 500 sidebar request.user.username %}
        .. sidebar for logged in user ..
    {% endcache %}

如果 USE_I18N 设置为 True， 则每站点中间件缓存将遵循活动语言 [respect the active language](https://docs.djangoproject.com/en/2.1/topics/cache/#i18n-cache-key) 。 对于缓存模板标记， 您可以使用模板中可用的特定于转换的变量 [translation-specific variables](https://docs.djangoproject.com/en/2.1/topics/i18n/translation/#template-translation-vars) 之一来实现相同的结果：

    {% load i18n %}
    {% load cache %}
    
    {% get_current_language as LANGUAGE_CODE %}
    
    {% cache 600 welcome LANGUAGE_CODE %}
        {% trans "Welcome to example.com" %}
    {% endcache %}

缓存超时时间可以是模板变量， 只要模板变量解析为整数值即可。 例如， 如果模板变量 my_timeout 设置为值600， 则以下两个示例是等效的：、

    {% cache 600 sidebar %} ... {% endcache %}
    {% cache my_timeout sidebar %} ... {% endcache %}

此功能有助于避免模板中的重复。 您可以在一个位置设置变量中的超时时间， 然后只重用该值。

默认情况下， 缓存标记将尝试使用名为 “template_fragments” 的缓存。 如果不存在此类缓存， 则它将回退到使用默认缓存。 您可以选择备用缓存后端以与 using 关键字参数一起使用， 该参数必须是标记的最后一个参数。

    {% cache 300 local-thing ...  using="localcache" %}

指定未配置的缓存名称被视为错误。

**django.core.cache.utils.make_template_fragment_key(fragment_name, vary_on=None)**

如果要获取用于缓存片段的缓存密钥， 可以使用 make_template_fragment_key.fragment_name 与缓存模板标记的第二个参数相同; vary_on 是传递给标记的所有其他参数的列表。 此函数可用于使缓存项无效或被覆盖， 例如：

    >>> from django.core.cache import cache
    >>> from django.core.cache.utils import make_template_fragment_key
    # cache key for {% cache 500 sidebar username %}
    >>> key = make_template_fragment_key('sidebar', [username])
    >>> cache.delete(key) # invalidates cached template fragment

-------------

#### The low-level cache API

有时候， 缓存整个渲染页面并不会给你带来太大的好处， 实际上是不方便的过度杀伤(inconvenient overkill)。

例如， 您的站点可能包含一个视图， 其结果取决于几个昂贵的查询， 其结果会在不同的时间间隔内发生变化。 在这种情况下， 使用每站点或每个视图缓存策略提供的整页缓存并不理想， 因为您不希望缓存整个结果（因为某些数据经常更改）， 但你仍然想要缓存很少改变的结果。

对于这样的情况， Django公开了一个简单的低级缓存API。 您可以使用此API以任意级别的粒度在缓存中存储对象。 您可以缓存任何可以安全序列化(pickled)的Python对象： 字符串， 字典， 模型对象列表等。 （大部分的Python对象都可以被序列化; 有关序列化(pickling)的更多信息， 请参阅Python文档。）

##### Accessing the cache

django.core.cache.caches

您可以通过 dict-like 的对象访问在 CACHES 设置中配置好的缓存： django.core.cache.caches。 在同一个线程中对同一别名的重复请求将返回相同的对象。

    >>> from django.core.cache import caches
    >>> cache1 = caches['myalias']
    >>> cache2 = caches['myalias']
    >>> cache1 is cache2
    True

如果指定的键不存在， 将引发 InvalidCacheBackendError 错误。

为了提供线程安全性， 将为每个线程返回缓存后端的不同实例。

django.core.cache.cache

作为快捷方式， 默认缓存可用作 django.core.cache.cache：

    >>> from django.core.cache import cache

该对象相当于 caches['default']。
    
-------------

##### Basic usage

基本接口是：

cache.set(key, value, timeout=DEFAULT_TIMEOUT, version=None)

    >>> cache.set('my_key', 'hello, world!', 30)

cache.get(key, default=None, version=None)

    >>> cache.get('my_key')
    'hello, world!'

key 应该是一个 str， value 可以是任何可序列化(picklable)的Python对象。

timeout参数是可选的， 默认为CACHES设置中相应后端的超时参数（如上所述）。 它的值是秒， 并应被存储在缓存中。 为超时传递 None 将永远缓存该值。 timeout 设为0则不会缓存该值。

如果缓存中不存在该对象， 则 cache.get() 返回 None：

    >>> # Wait 30 seconds for 'my_key' to expire...
    >>> cache.get('my_key')
    None

我们建议不要在缓存中存储字面值 None， 因为您将无法区分存储的 None 值和由返回值 None 表示的缓存未命中。

cache.get() 可以采用 default 参数。 如果缓存中不存在该对象， 则返回默认值：

    >>> cache.get('my_key', 'has expired')
    'has expired'

cache.add(key, value, timeout=DEFAULT_TIMEOUT, version=None)

要仅在密钥尚不存在时添加密钥， 请使用 add() 方法。 它采用与 set() 相同的参数， 但如果指定的键已存在， 则不会尝试更新缓存：

    >>> cache.set('add_key', 'Initial value')
    >>> cache.add('add_key', 'New value')
    >>> cache.get('add_key')
    'Initial value'

如果您需要知道 add() 是否在缓存中存储了值， 可以检查返回值。 如果存储了值， 它将返回 True， 否则返回 False。

cache.get_or_set(key, default, timeout=DEFAULT_TIMEOUT, version=None)

如果想要获取键值或者设置键值， 而键又不在缓存中， 可以用 get_or_set() 方法。 它采用与 get() 相同的参数， 但默认设置为该键的新缓存值， 而不是简单地返回：

    >>> cache.get('my_new_key')  # returns None
    >>> cache.get_or_set('my_new_key', 'my new value', 100)
    'my new value'

您还可以将任何可调用的值作为 *default* 值传递：

    >>> import datetime
    >>> cache.get_or_set('some-timestamp-key', datetime.datetime.now)
    datetime.datetime(2014, 12, 11, 0, 15, 49, 457920)

cache.get_many(keys, version=None)

还有一个 get_many() 接口只能访问缓存一次。 get_many() 返回一个字典， 其中包含您请求的所有实际存在于缓存中（并且尚未过期）的键：

    >>> cache.set('a', 1)
    >>> cache.set('b', 2)
    >>> cache.set('c', 3)
    >>> cache.get_many(['a', 'b', 'c'])
    {'a': 1, 'b': 2, 'c': 3}

cache.set_many(dict, timeout)

要更有效地设置多个值， 请使用 set_many() 传递键值对的字典：

    >>> cache.set_many({'a': 1, 'b': 2, 'c': 3})
    >>> cache.get_many(['a', 'b', 'c'])
    {'a': 1, 'b': 2, 'c': 3}

与 cache.set() 类似， set_many() 采用可选的 timeout 参数。

在支持的后端（memcached）上， set_many() 返回无法插入的键列表。

> 在Django 2.0中更改：
> 包含失败键列表的返回值已添加。

cache.delete(key, version=None)

您可以使用 delete() 显式删除键。 这是清除特定对象的缓存的简单方法：

    >>> cache.delete('a')

cache.delete_many(keys, version=None)

如果要一次清除一批键， 可以用 delete_many() 来清除键列表：

    >>> cache.delete_many(['a', 'b', 'c'])

cache.clear()

最后， 如果要删除缓存中的所有键， 请使用 cache.clear()。 小心使用这个; clear() 将从缓存中删除所有内容， 而不仅仅是应用程序设置的密钥。

    >>> cache.clear()

cache.touch(key, timeout=DEFAULT_TIMEOUT, version=None)

> New in Django 2.1:

cache.touch() 为键设置新的过期时间。 例如， 要将键更新为从现在起10秒后过期：

    >>> cache.touch('a', 10)
    True

与其他方法一样， timeout 参数是可选的， 默认为 CACHES 设置中相应后端的 TIMEOUT 选项。

如果成功对键执行了 touch()， 则 touch() 返回 True， 否则返回 False。

cache.incr(key, delta=1, version=None)

cache.decr(key, delta=1, version=None)

您还可以分别使用 incr() 或 decr() 方法递增或递​​减已存在的键。 默认情况下， 现有缓存值将递增或递减1. 可以通过为递增/递减调用提供参数来指定其他递增/递减值。 如果您尝试递增或递减不存在的缓存键， 将引发 ValueError：

    >>> cache.set('num', 1)
    >>> cache.incr('num')
    2
    >>> cache.incr('num', 10)
    12
    >>> cache.decr('num')
    11
    >>> cache.decr('num', 5)
    6

> 注意
> incr()/decr() 方法不保证是原子的。 在那些支持原子递增/递减的后端（最特别的是， memcached后端）， 递增和递减操作将是原子的。 但是， 如果后端本身不提供递增/递减操作， 则将使用两步检索/更新来实现。

cache.close()

如果缓存由后端实现， 则可以使用 close() 关闭与缓存的连接。

    >>> cache.close()

> 注意
> 对于没有实现 close 方法的缓存， 它是一个no-op(空指令或者无操作)。

-------------

##### Cache key prefixing

如果要在服务器之间或生产环境与开发环境之间共享缓存实例， 则一台服务器缓存的数据可能会被另一台服务器使用。 如果服务器之间的缓存数据格式不同， 这可能会导致一些非常难以诊断的问题。

为了防止这种情况， Django提供了为服务器使用的所有缓存键添加前缀的功能。 当保存或检索特定的缓存键时， Django将自动为缓存键添加 KEY_PREFIX 缓存设置的值。

通过确保每个Django实例具有不同的KEY_PREFIX， 您可以确保缓存值中不会发生冲突。

-------------

##### Cache versioning

更改使用缓存值的运行代码时， 可能需要清除任何现有缓存值。 最简单的方法是刷新整个缓存， 但这可能会导致丢失仍然有效且有用的缓存值。

Django提供了一种更好的方法来定位单个缓存值。 Django的缓存框架具有系统范围的版本标识符， 使用 VERSION 缓存设置指定。 此设置的值将自动与缓存前缀和用户提供的缓存键组合以获取最终缓存键。

默认情况下， 任何键请求都将自动包含站点默认缓存键版本。 但是， 原始缓存函数都包含 version 参数， 因此您可以指定要设置或获取的特定缓存键版本。 例如：

    >>> # Set version 2 of a cache key
    >>> cache.set('my_key', 'hello world!', version=2)
    >>> # Get the default version (assuming version=1)
    >>> cache.get('my_key')
    None
    >>> # Get version 2 of the same key
    >>> cache.get('my_key', version=2)
    'hello world!'

可以使用 incr_version() 和 decr_version() 方法递增和递减特定键的版本。 这使得特定键可以碰撞到新版本， 而其他键不受影响(This enables specific keys to be bumped to a new version, leaving other keys unaffected.)。 继续前面的例子：

    >>> # Increment the version of 'my_key'
    >>> cache.incr_version('my_key')
    >>> # The default version still isn't available
    >>> cache.get('my_key')
    None
    # Version 2 isn't available, either
    >>> cache.get('my_key', version=2)
    None
    >>> # But version 3 *is* available
    >>> cache.get('my_key', version=3)
    'hello world!'

-------------

##### Cache key transformation

如前两节所述， 用户提供的缓存键不是逐字使用的 - 它与缓存前缀和键版本相结合， 以提供最终缓存键。 默认情况下， 使用冒号连接这三个部分以生成最终字符串：

    def make_key(key, key_prefix, version):
        return ':'.join([key_prefix, str(version), key])

如果要以不同方式组合部件， 或对最终键应用其他处理（例如， 获取关键部件的hash digest）， 则可以提供自定义键函数。

KEY_FUNCTION 缓存设置可以指定一个 dotted-path 的函数， 且与上面的 make_key() 原型匹配。 如果提供了， 将使用此自定义键函数而不是默认键组合函数。

-------------

##### Cache key warnings

Memcached是最常用的生产缓存后端， 它不允许超过250个字符的缓存键或包含空格或控制字符， 如果使用此类键会导致异常。 为了鼓励缓存可移植代码并最大限度地减少令人不快的意外， 如果使用会导致memcached错误的密钥， 则其他内置缓存后端会发出警告(django.core.cache.backends.base.CacheKeyWarning)。
(Memcached, the most commonly-used production cache backend, does not allow cache keys longer than 250 characters or containing whitespace or control characters, and using such keys will cause an exception. To encourage cache-portable code and minimize unpleasant surprises, the other built-in cache backends issue a warning (django.core.cache.backends.base.CacheKeyWarning) if a key is used that would cause an error on memcached.)

如果您使用的生产后端可以接受更广泛的键（自定义后端或其中一个非memcached内置后端）， 并希望在没有警告的情况下使用更宽范围， 则可以使用此代码使 CacheKeyWarning 静音在您的一个 INSTALLED_APPS 的 management 模块中：
(If you are using a production backend that can accept a wider range of keys (a custom backend, or one of the non-memcached built-in backends), and want to use this wider range without warnings, you can silence CacheKeyWarning with this code in the management module of one of your INSTALLED_APPS:)

    import warnings
    
    from django.core.cache import CacheKeyWarning
    
    warnings.simplefilter("ignore", CacheKeyWarning)

如果您想为其中一个内置后端提供自定义键验证逻辑， 则可以对其进行子类化， 仅覆盖 validate_key 方法， 并按照使用自定义缓存后端 [using a custom cache backend](https://docs.djangoproject.com/en/2.1/topics/cache/#using-a-custom-cache-backend) 的说明进行操作。 例如， 要为 locmem 后端执行此操作， 请将以下代码放在模块中：

    from django.core.cache.backends.locmem import LocMemCache
    
    class CustomLocMemCache(LocMemCache):
        def validate_key(self, key):
            """Custom validation, raising exceptions or warnings as needed."""
            ...

...并在 CACHES 设置的 BACKEND 部分中使用 dotted Python 路径指向这个类。

-------------

#### Downstream caches

到目前为止， 本文档主要关注缓存您自己的数据。 但另一种类型的缓存也与Web开发相关： 由“下游”缓存执行的缓存。 这些系统甚至在请求到达您的网站之前就会为用户缓存页面。

以下是下游缓存的一些示例：

- 您的 ISP 可能会缓存某些页面， 因此如果您从 https://example.com/ 请求了某个页面， 您的 ISP 可能会向您发送该页面而无需直接访问 example.com。 example.com 的维护者不知道这个缓存; ISP 位于 example.com 和您的 Web 浏览器之间， 透明地处理所有缓存。

- 您的 Django 网站可能位于代理缓存之后， 例如 Squid Web 代理缓存（http://www.squid-cache.org/）， 它会缓存页面以提高性能。 在这种情况下， 每个请求首先由代理处理， 只有在需要时才会传递给您的应用程序。

- 您的 Web 浏览器也会缓存页面。 如果网页发出相应的头部， 您的浏览器将使用本地缓存副本来获取对该页面的后续请求， 甚至无需再次联系网页以查看其是否已更改。

下游缓存可以很好的提升效率， 但它有一个危险： 许多网页的内容根据身份验证和许多其他变量而有所不同， 并且基于 URL 盲目保存页面的缓存系统可能会将不正确或敏感数据暴露给后续
这些页面的访问者。

例如， 假设您运行 Web 电子邮件系统， “收件箱”页面的内容显然取决于登录的用户。 如果 ISP 盲目缓存您的站点， 那么通过该 ISP 登录的第一个用户将拥有他们的
为后续访问该网站的用户缓存的特定于用户的收件箱页面。 这就不好了。

幸运的是， HTTP 提供了解决此问题的方法。 存在许多HTTP头以指示下游缓存根据指定的变量区分其缓存内容， 并告知缓存机制不缓存特定页面。 我们将在后面的部分中介绍其中的一些头部。

-------------

#### Using Vary headers

Vary 头定义了缓存机制在构建其缓存键时应考虑的请求头。 例如， 如果网页的内容取决于用户的语言设置， 则该页面被称为“因语言而异”。

默认情况下， Django的缓存系统使用请求的完全限定(fully-qualified) URL 创建其缓存键 - 例如，“https://www.example.com/stories/2005/?order_by=author”。 这意味着对该 URL 的每个请求都将使用相同的缓存版本， 无论用户代理差异如cookie或语言设置如何。 但是， 如果此页面根据请求头中的某些差异（例如cookie， 语言或用户代理）生成不同的内容， 则需要使用 Vary 头来告知页面输出所依赖的缓存机制。

要在Django中执行此操作， 请使用方便的 django.views.decorators.vary.vary_on_headers() 视图装饰器， 如下所示：

    from django.views.decorators.vary import vary_on_headers
    
    @vary_on_headers('User-Agent')
    def my_view(request):
        ...



