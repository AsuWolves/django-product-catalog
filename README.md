# Django Product Catalog

A small Django project that models **products**, **categories**, and **tags**, with a
single page that lets you **search products by description** and **filter them by
category and tags** — in any combination.

## Tech stack

- Python 3.12, Django 5.2 (LTS)
- SQLite (default Django database)
- Server-rendered Django templates (no front-end build step, no JavaScript framework)

## Data model

| Model      | Key fields                                                | Relationships |
|------------|-----------------------------------------------------------|---------------|
| `Category` | `name` (unique), `description`                            | —             |
| `Tag`      | `name` (unique)                                           | —             |
| `Product`  | `name`, `description`, `price`, `created_at`              | `category` → **ForeignKey** to `Category` (one category per product); `tags` → **ManyToMany** to `Tag` |

## Setup and run

```bash
# 1. Clone the repo, then from the project root:
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply migrations (no-op on a fresh clone — the database is already included)
python manage.py migrate

# 4. Run the development server
python manage.py runserver
```

Then open:

- **Search / filter page:** http://127.0.0.1:8000/
- **Django admin:** http://127.0.0.1:8000/admin/

### Admin login

A demo superuser is included with the committed database:

- **Username:** `admin`
- **Password:** `adminpass123`

(If you ever start from an empty database, create your own with
`python manage.py createsuperuser`.)

## Using the search page

The page at `/` has one form combining three controls:

- **Search** — matches text against the product *description* (case-insensitive, partial).
- **Category** — a dropdown to restrict results to a single category.
- **Tags** — checkboxes to restrict results to products carrying *any* of the selected tags.

All three apply together, so you can e.g. search "wireless", pick *Electronics*, and check
*Premium* at once. **Clear** resets all filters.

## How the querying works

All filtering lives in `catalog/views.py` (`product_list`). Filters are applied as a
chained queryset, so combining them narrows the results:

```python
products = Product.objects.select_related('category').prefetch_related('tags')

if query:
    products = products.filter(description__icontains=query)
if category_id:
    products = products.filter(category_id=category_id)
if selected_tag_ids:
    products = products.filter(tags__in=selected_tag_ids).distinct()
```

- `select_related('category')` and `prefetch_related('tags')` keep the page to a small,
  constant number of queries (avoids the N+1 problem when rendering the table).
- The tag filter uses `tags__in=[...]` with `.distinct()` — **OR** semantics, i.e. a
  product matches if it has *any* of the chosen tags.
- The `category` and `tags` parameters are validated before querying: non-numeric values
  (e.g. `?category=abc`) are ignored rather than allowed to raise an error, so a malformed
  URL still returns a normal page.

## Sample data

The committed `db.sqlite3` is pre-populated with **6 categories, 12 tags, and 25
products** (above the assignment's 5 / 10 / 20 minimums). One product is intentionally
left without any tags to exercise the optional-tags case. All of this data is managed
through the registered Django admin (`catalog/admin.py`), where `Product` has search,
category/tag list filters, and a horizontal tag selector. You can add, edit, or remove
records from `/admin/` and the search page will reflect the changes immediately.

## Tests

```bash
python manage.py test
```

The suite (`catalog/tests.py`) covers the model relationships (FK + M2M, both
directions) and the view: description search (hit/miss), category filter, single- and
multi-tag filtering (OR semantics), combined filters, and graceful handling of invalid
or non-numeric URL parameters.

## Assumptions and notes

- **One category per product** (ForeignKey); a product can have **many tags** (ManyToMany).
- A product **must have a category** (the field is required, so the admin rejects a blank
  category), but it **may have zero tags** (tags are optional).
- **Search targets the description field**, as specified by the assignment.
- **Tag filtering is OR**: selecting multiple tags returns products matching any of them.
- The `db.sqlite3` file is intentionally **committed** so the project has data on clone;
  it is therefore *not* listed in `.gitignore`.
- `DEBUG = True` and the inline `SECRET_KEY` in `config/settings.py` are for this demo
  only and are not production-safe.

## AI assistance (Claude Code)

Per the assignment's disclosure requirement, this project was built with the help of
**Claude Code** (Anthropic's CLI coding agent), used as follows:

- **Planning** — I used Claude Code's plan mode to turn the assignment brief into an
  implementation plan. It asked clarifying questions about the design (category as a
  ForeignKey vs ManyToMany, how to populate and ship the sample data, and server-rendered
  templates vs an API/JS frontend); I made those decisions and it produced a structured
  plan.
- **Code generation** — From that plan, Claude Code spawned subagents to implement the tasks
  and I reviewed its outputs: the models (`catalog/models.py`), admin config (`catalog/admin.py`),
  the search/filter view (`catalog/views.py`), URLs, the HTML template, and the test suite (`catalog/tests.py`),
  as well as this README and `CLAUDE.md`.
- **Sample data** — In Django admin, I generated the seed categories/tags/products stored in the
  committed `db.sqlite3`.
- **Debugging & refinement** — I tested the app and surfaced edge cases (e.g. non-numeric
  `category`/`tags` URL parameters that errored); Claude added input validation and
  regression tests for them.
- **My role** — I directed the requirements and design choices, reviewed all generated
  code, ran and tested the app, and am responsible for the final result.
