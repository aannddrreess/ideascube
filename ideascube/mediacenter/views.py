from urllib.parse import urlparse

from django.core.urlresolvers import reverse_lazy, resolve, Resolver404
from django.db.models import F
from django.db.models.functions import Lower
from django.http import Http404, JsonResponse
from django.template.loader import render_to_string
from django.utils.translation import get_language, ugettext_lazy as _
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from ideascube.decorators import staff_member_required
from ideascube.mixins import FilterableViewMixin, OrderableViewMixin

# For unittesting purpose, we need to mock the Catalog class.
# However, the mock is made in a fixture and at this moment, we don't
# know where the mocked catalog will be used.
# So the fixture mocks 'ideascube.serveradmin.catalog.Catalog'.
# If we want to use the mocked Catalog here, we must not import the
# Catalog class directly but reference it from ideascube.serveradmin.catalog
# module.
from ideascube.serveradmin import catalog as catalog_mod

from .models import Document
from .forms import DocumentForm


class Index(FilterableViewMixin, OrderableViewMixin, ListView):

    ORDERS = [
        {
            'key': 'modified_at',
            'label': _('Last modification'),
            'expression': F('modified_at'),
            'sort': 'desc'
        },
        {
            'key': 'title',
            'label': _('Title'),
            'expression': Lower('title'),  # Case insensitive.
            'sort': 'asc'
        }
    ]

    model = Document
    template_name = 'mediacenter/index.html'
    paginate_by = 24

    def _set_available_kinds(self, context):
        available_kinds = self._search_for_attr_from_context('kind', context)
        context['available_kinds'] = [
            (kind, label) for kind, label in Document.KIND_CHOICES
            if kind in available_kinds]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self._set_available_kinds(context)
        self._set_available_langs(context)
        self._set_available_tags(context)
        # We assume that if there is a source, it is a package_id.
        package_id = context.get('source')
        if package_id:
            catalog = catalog_mod.Catalog()
            try:
                package = catalog.list_installed([package_id])[0]
            except IndexError:
                # We cannot find the package.
                # This should not happen. Remove the filter
                del context['source']
                return context

            context['source_name'] = package.name
        return context

index = Index.as_view()


class DocumentDetail(DetailView):
    model = Document
document_detail = DocumentDetail.as_view()


class DocumentUpdate(UpdateView):
    model = Document
    form_class = DocumentForm
document_update = staff_member_required(DocumentUpdate.as_view())


class DocumentCreate(CreateView):
    model = Document
    form_class = DocumentForm
    initial = {
        'lang': get_language(),
    }
document_create = staff_member_required(DocumentCreate.as_view())


class DocumentDelete(DeleteView):
    model = Document
    success_url = reverse_lazy('mediacenter:index')
document_delete = staff_member_required(DocumentDelete.as_view())


class OEmbed(DetailView):
    model = Document
    template_name = 'mediacenter/oembed.html'

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        url = self.request.GET.get('url')
        if not url:
            raise Http404()
        parsed = urlparse(url)
        try:
            match = resolve(parsed.path)
        except Resolver404:
            raise Http404()
        if 'pk' not in match.kwargs:
            raise Http404()
        return queryset.get(pk=match.kwargs['pk'])

    def render_to_response(self, context, **response_kwargs):
        html = render_to_string(self.get_template_names(), context=context)
        return JsonResponse({
            "html": html,
            "type": "rich"
        })

oembed = OEmbed.as_view()
