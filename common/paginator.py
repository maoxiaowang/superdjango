from django.core.paginator import Paginator, Page as _Page
from django.utils.functional import cached_property
from pymongo.cursor import Cursor

__all__ = [
    'Paginator',
    'MongoPaginator'
]


class MongoPage(_Page):

    def __len__(self):
        return self.paginator.count()


class MongoPaginator(Paginator):

    def __init__(self, *args, **kwargs):
        # In order to be fitted with collection.document_count()
        # self.total_count = kwargs.get('total_count')
        # kwargs.pop('total_count')
        super().__init__(*args, **kwargs)

    def page(self, number):
        """Return a Page object for the given 1-based page number."""
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        # top = bottom + self.per_page
        # if top + self.orphans >= self.count:
        #     top = self.count
        # if isinstance(self.object_list, list):
        #     object_list = [] if not self.object_list else self.object_list[bottom: bottom+self.per_page]
        # else:

        object_list = [] if not isinstance(self.object_list, Cursor) else self.object_list.skip(
            bottom).limit(self.per_page)
        return self._get_page(object_list, number, self)

    @cached_property
    def count(self):
        """Return the total number of objects, across all pages."""
        # if self.total_count:
        #     return self.total_count
        try:
            return self.object_list.count()
        except (AttributeError, TypeError):
            # AttributeError if object_list has no count() method.
            # TypeError if object_list.count() requires arguments
            # (i.e. is of type list).
            return len(self.object_list)

    def _get_page(self, *args, **kwargs):
        """
        Return an instance of a single page.

        This hook can be used by subclasses to use an alternative to the
        standard :cls:`Page` object.
        """
        return MongoPage(*args, **kwargs)
