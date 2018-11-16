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


















































































