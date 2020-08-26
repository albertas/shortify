# Shortify
Website for URL shortening.

# Setup and run project using `docker-compose up`
* Install `docker-ce` and `docker-compose` (check if its setup correctly by running `docker run hello-world`)
* `git clone https://github.com/albertas/shortify`  # Clones this repository
* `cd shortify`  # Goes to project directory
* `make`  # Builds docker images, prepares and starts containers. Then connects to django
  container. Following commands should be executed inside django container.
* `make test`  # Executes automated tests to see if everything was setup correctly
* `make migrate`  # Creates SQL schemas in the local PosgresSQL database
* `make run`  # Starts local development server which can be accessed at [localhost:8000](http://localhost:8000) and
  admin page at [localhost:8000/admin/](http://localhost:8000/admin/)

# Setup and run project without docker
* `git clone https://github.com/albertas/shortify`  # Clones this repository
* `cd shortify`  # Goes to project directory
* `python3 -m venv venv`  # Prepares Python virtual env
* `venv/bin/pip install -r requirements.txt`  # installs dependencies to it
* `venv/bin/python manage.py test --settings=shortify.settings.test`  # Executes automated tests to see if everything was setup correctly
* `venv/bin/python manage.py migrate --settings=shortify.settings.test`  # Creates local SQLite3 database and prepares it for usage
* `venv/bin/python manage.py runserver --settings=shortify.settings.test`  # Starts local development server which can be accessed at [localhost:8000](http://localhost:8000),
   and admin page at [localhost:8000/admin/](http://localhost:8000/admin/)

# Considered decisions
## What max URL length has to be allowed?
Max length of URLs submitted by users has to be restricted in order to avoid database flooding attacks.
Hence Django URLField, which requires predefined max length can be used instead of TextField for
storing URLs.

In order to make our URL shortening service as usable as possible we should choose quite loose URL
length restriction. For example, 8190 bytes would be a good option, because its maximum rational
size base on Gunicorn, see: https://docs.gunicorn.org/en/stable/settings.html#limit-request-line

## How to optimize `redirect_short_to_long` view?
In this section we will investigate and quantitatively evaluate several ways to improve
performance of `redirect_short_to_long_url()` view, which
covers several features like:
* redirects from short URL to the original one,
* records timestamp, IP address, HTTP Referer for each shortened URL click,
* deactivates the shortened URL, when maximum number of clicks is set and reached,
* deactivates the shortened URL, when expiration date-time is set and reached.

PostgreSQL database will be used for this investigation, since its one of the most likely options
for production environments. Performance comparison of database backends is out of scope of this
investigation. The database will be filled with 100000 shortened URLs to better reflect real
world setup and to increase durations of inefficient SQL queries. `django-silk` profiler was chosen
to evaluate HTTP response time and database query durations.

Performance aspects which will be investigated:
1. Usage of database indexes:
 - 1.1. short url path is separate column with `db_index=False`.
 - 1.2. short url path is separate column with `db_index=True`.
 - 1.3. short url path is primary key (`db_index=True` by default).
2. Way to calculate the number of clicks shortened URL already has:
 - 2.1. Calculating click objects in order to determine if max number of clicks was reached
 - 2.2. Having a separate click counter, but its updated as a separate database call
 - 2.3. Having a separate click counter and its value is updated using `post_save` signal of the Click log record (this database hit is out of view scope)
3. Do not retrieve unused data of a shortened URL:
 - 3.1. Retrieving whole shortened URL object
 - 3.2. Retrieving only the URL
4. Using raw SQL statements instead of ORM to form the SQL statement.
 - 4.1. ORM is used to create SQL queries.
 - 4.2. Raw SQL queries are hardcoded completely overcoming ORM usage.
5. Usage of synchronous VS asynchronous views (became available from Django 3.1). Database queries
   are still made synchronously, asynchronous database will be available only from Django 4.0.
 - 5.1. Synchronous view
 - 5.2. Asynchronous view when Click objects creation is awaited
 - 5.3. Asynchronous view when Click objects creation is executed as separate async task


### 1. Usage of database indexes
Lets start with completely unoptimized 1.1. version of [`redirect_short_to_long()`](https://github.com/albertas/shortify/blob/master/shortify/views.py#L25) view:

``` lang-python
01 def redirect_short_to_long_url(request, short_path):
02     try:
03         shortened_url = ShortenedURL.objects.get(
04             Q(short_path=short_path),
05             Q(is_active=True),
06             Q(deactivate_at__isnull=True) | Q(deactivate_at__gt=timezone.now()),
07         )
08         if shortened_url.max_clicks and shortened_url.max_clicks <= shortened_url.click_set.count():
09             raise Http404
10     except ShortenedURL.DoesNotExist:
11         raise Http404
12     Click.objects.create(
13         shortened_url_id=short_path,
14         ip=request.META.get("REMOTE_ADDR"),
15         http_referer=request.META.get("HTTP_REFERER"),
16     )
17     return HttpResponsePermanentRedirect(shortened_url.url)
```

In 1.1. Version `ShortenedURL.short_path` field has `db_index=False`, because it is set by default:

```
18 class ShortenedURL(models.Model):
19     short_path = models.CharField(max_length=6, default=gen_short_path)
20     url = models.URLField(max_length=8190)
21     is_active = models.BooleanField(default=True)
22     deactivate_at = models.DateTimeField(null=True)
```

In 1.2. version its `db_index=True`:

```
18     short_path = models.CharField(max_length=6, default=gen_short_path, db_index=True)
```

In 1.3. version `short_path` is updated to be primary key:

```
18     short_path = models.CharField(primary_key=True, max_length=6, default=gen_short_path)
```

Database was filled with 100000 shortened URL records and one of them
was opened 100 times (using `requests` package) for each version.
Maximum HTTP response time and
maximum SQL query duration was evaluated using `django-silk` profiler:

|                                | 1.1. | 1.2. | 1.3. |
| -------------------------------| --|--|--|
| Max HTTP response time     | 85ms | 38ms | 34ms |
| Max SQL query duration     | 36ms | 6ms | 5ms |

#### Conclusion
Conclusion can be drawn that the most efficient strategy is 1.3. - to store `ShortenedURL.short_path` as primary key.

### 2. Way to calculate the number of clicks shortened URL already has
Each shortened URL click creates a separate `Click` record in the database.
To disable shortened URL after fixed number of clicks, number of `Click` records has to be counted
for that URL, which is time consuming operation.
Lets improve the 1.3. version code by selecting the best strategy for counting number of clicks. 2.1.
version matches 1.3. version and is as follows:

```
01 def redirect_short_to_long_url(request, short_path):
02     try:
03         shortened_url = ShortenedURL.objects.get(
04             Q(pk=short_path),
05             Q(is_active=True),
06             Q(deactivate_at__isnull=True) | Q(deactivate_at__gt=timezone.now()),
07         )
08         if shortened_url.max_clicks and shortened_url.max_clicks <= shortened_url.click_set.count():
09             raise Http404
10     except ShortenedURL.DoesNotExist:
11         raise Http404
12     Click.objects.create(
13         shortened_url_id=short_path,
14         ip=request.META.get("REMOTE_ADDR"),
15         http_referer=request.META.get("HTTP_REFERER"),
16     )
17     return HttpResponsePermanentRedirect(shortened_url.url)
```

Counting operation can be avoided if a counter value is stored in the database.
In 2.2. version we will have a separate click counter:

```
01 class ShortenedURL(models.Model):
02     number_of_clicks = models.PositiveIntegerField(default=0)
03     ...
```

To updating the counter would require additional database hit during shortened URL redirection.

```
04 def redirect_short_to_long_url(request, short_path):
05     try:
06         url, number_of_clicks = ShortenedURL.objects.filter(
07             Q(pk=short_path),
08             Q(is_active=True),
09             Q(deactivate_at__isnull=True) | Q(deactivate_at__gt=timezone.now()),
10             Q(max_clicks__isnull=True) | Q(number_of_clicks__lte=F("max_clicks"))
11         ).values_list('url', 'number_of_clicks')[0]
12     except IndexError:
13         raise Http404
14
15     ShortenedURL.objects.filter(pk=short_path).update(number_of_clicks=number_of_clicks + 1)
16
17     Click.objects.create(
18         shortened_url_id=short_path,
19         ip=request.META.get("REMOTE_ADDR"),
20         http_referer=request.META.get("HTTP_REFERER"),
21     )
22     return HttpResponsePermanentRedirect(shortened_url.url)
```

`Click.post_save` signal usage probably could move this database hit can be of URL redirection view
to. This will be done In 2.3. version. So, `number_of_clicks` value and 15 line of 2.2 version is
removed and this `Click.post_save` signal handler is added in 2.3. version:

```
24 @receiver(post_save, sender=Click)
25 def increase_click_counter(sender, signal, instance, created, update_fields, **kwargs):
26     if created:
27         instance.shortened_url.number_of_clicks += 1
28         instance.shortened_url.save()
```

|                                        | 2.1. | 2.2. | 2.3. |
| ---------------------------------------|--|--|--|
| Max SQL query duration (0 clicks)      | 11.7ms | 21.1ms | 21.6ms |
| Max SQL query duration (10000 clicks)  | 11.7ms | 21.1ms | 21.6ms |

#### Conclusions
The first conclusion of this part is that `django-silk` is not very good profiler, it omits
creation and raw SQL queries from its summaries. Another profiling strategy was chosen: to use
`django-debug-toolbar` overviews, since they are more acurate and reliable.

Another conclusion is based on `django-debug-toolbar`: there is no performance difference between
2.2 and 2.3 strategies, hence there is no point of useing `Click.post_save` signal.

The final conclusion is that 2.1 version is superior over 2.2, since counter update operation always takes about 10ms,
but selecting Click count takes less than 1ms when database size is relatively small (<100000 records).
However `Count()` operation tends to take longer when database size grows, because it has to do
full table scan each time: https://www.postgresqltutorial.com/postgresql-count-function/ It would
be way better to have click counter and update it outside of `redirect_short_to_long()` view. This
should be possible with async views.

### 3. Do not retrieve unused data of a shortened URL

These two versions were considered:
 - 3.1. Retrieving all ShortenedURL instance fields
 - 3.2. Retrieving only the needed `url` and `max_clicks` fields.

|                                        | 3.1. | 3.2. |
| ---------------------------------------|--|--|
| Max SQL query duration (0 clicks)      | 11.7ms | 11.2ms |

#### Conclusions
Retrieving only needed data from database gives a slight performance improvement 11.2ms vs 11.7ms.
In our case the improvement is marginal (even could be deviation error), however if `ShortenedURL`
had larger fields, like text fields, the improvement would be greater.

### 4. Using raw SQL statements instead of ORM to form the SQL statement.
Not investigated.

### 5. Usage of synchronous VS asynchronous views (became available from Django 3.1).
These two versions were considered:
 - 5.1. Synchronous view
 - 5.2. Asynchronous view when `Click` object's creation is awaited
 - 5.3. Asynchronous view when `Click` object's creation is executed as separate async task

|                                        | 5.1. | 5.2. | 5.3 |
| ---------------------------------------|--|--|--|
| Total HTTP response time               | 80ms | 50ms | 30ms |

#### Conclusions
Asynchronous view usage has way better performance, however with a code testability trade off.
Debuging and testing of async views are more complicated.
