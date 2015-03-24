import pytest
from django.core.urlresolvers import reverse

from ideasbox.tests.factories import UserFactory

from ..models import Entry, Inventory, InventorySpecimen, Specimen, StockItem
from .factories import (EntryFactory, InventoryFactory, SpecimenFactory,
                        StockItemFactory)

pytestmark = pytest.mark.django_db


def test_anonymous_should_not_access_entry_page(app):
    assert app.get(reverse('monitoring:entry'), status=302)


def test_non_staff_should_not_access_entry_page(loggedapp):
    assert loggedapp.get(reverse('monitoring:entry'), status=302)


def test_staff_should_access_entry_page(staffapp):
    assert staffapp.get(reverse('monitoring:entry'), status=200)


@pytest.mark.parametrize('module', [m[0] for m in Entry.MODULES])
def test_can_create_entries(module, staffapp):
    UserFactory(serial='123456')
    assert not Entry.objects.count()
    form = staffapp.get(reverse('monitoring:entry')).forms['entry_form']
    form['serials'] = '123456'
    form.submit('entry_' + module).follow()
    assert Entry.objects.count()


def test_anonymous_should_not_access_export_entry_url(app):
    assert app.get(reverse('monitoring:export_entry'), status=302)


def test_non_staff_should_not_access_export_entry_url(loggedapp):
    assert loggedapp.get(reverse('monitoring:export_entry'), status=302)


def test_staff_should_access_export_entry_url(staffapp):
    assert staffapp.get(reverse('monitoring:export_entry'), status=200)


def test_export_entry_should_return_csv_with_entries(staffapp, settings):
    EntryFactory.create_batch(3)
    settings.MONITORING_ENTRY_EXPORT_FIELDS = []
    resp = staffapp.get(reverse('monitoring:export_entry'), status=200)
    assert resp.content.startswith("module,date\r\ncinema,")
    assert resp.content.count("cinema") == 3


def test_anonymous_should_not_access_stock_page(app):
    assert app.get(reverse('monitoring:stock'), status=302)


def test_non_staff_should_not_access_stock_page(loggedapp):
    assert loggedapp.get(reverse('monitoring:stock'), status=302)


def test_staff_should_access_stock_page(staffapp):
    assert staffapp.get(reverse('monitoring:stock'), status=200)


def test_anonymous_should_not_access_stockitem_create_page(app):
    assert app.get(reverse('monitoring:stockitem_create'), status=302)


def test_non_staff_should_not_access_stockitem_create_page(loggedapp):
    assert loggedapp.get(reverse('monitoring:stockitem_create'), status=302)


def test_staff_should_access_stockitem_create_page(staffapp):
    assert staffapp.get(reverse('monitoring:stockitem_create'), status=200)


def test_staff_can_create_stockitem(staffapp):
    url = reverse('monitoring:stockitem_create')
    form = staffapp.get(url).forms['model_form']
    assert not StockItem.objects.count()
    form['module'] = StockItem.LIBRARY
    form['name'] = 'My stock item'
    form.submit().follow()
    assert StockItem.objects.count()


def test_staff_can_update_stockitem(staffapp):
    item = StockItemFactory(module=StockItem.DIGITAL)
    url = reverse('monitoring:stockitem_update', kwargs={'pk': item.pk})
    form = staffapp.get(url).forms['model_form']
    form['module'] = StockItem.LIBRARY
    form.submit().follow()
    assert StockItem.objects.get(pk=item.pk).module == StockItem.LIBRARY


def test_staff_can_create_specimen(staffapp):
    item = StockItemFactory()
    url = reverse('monitoring:specimen_create', kwargs={'item_pk': item.pk})
    form = staffapp.get(url).forms['model_form']
    assert not item.specimens.count()
    form['barcode'] = '23135321'
    form.submit().follow()
    assert item.specimens.count()


def test_staff_can_edit_specimen(staffapp):
    specimen = SpecimenFactory(count=3)
    url = reverse('monitoring:specimen_update', kwargs={'pk': specimen.pk})
    form = staffapp.get(url).forms['model_form']
    form['count'] == 3
    form['count'] = 4
    form.submit().follow()
    assert Specimen.objects.get(pk=specimen.pk).count == 4


def test_anonymous_should_not_access_inventory_create_page(app):
    assert app.get(reverse('monitoring:inventory_create'), status=302)


def test_non_staff_should_not_access_inventory_create_page(loggedapp):
    assert loggedapp.get(reverse('monitoring:inventory_create'), status=302)


def test_staff_should_access_inventory_create_page(staffapp):
    assert staffapp.get(reverse('monitoring:inventory_create'), status=200)


def test_staff_can_create_inventory(staffapp):
    url = reverse('monitoring:inventory_create')
    form = staffapp.get(url).forms['model_form']
    assert not Inventory.objects.count()
    form['made_at'] = '2015-03-22'
    form.submit().follow()
    assert Inventory.objects.count()


def test_staff_can_update_inventory(staffapp):
    inventory = InventoryFactory()
    url = reverse('monitoring:inventory_update', kwargs={'pk': inventory.pk})
    form = staffapp.get(url).forms['model_form']
    comments = 'A new comment'
    form['comments'] = comments
    form.submit().follow()
    assert Inventory.objects.get(pk=inventory.pk).comments == comments


def test_anonymous_should_not_access_inventory_detail_page(app):
    inventory = InventoryFactory()
    url = reverse('monitoring:inventory', kwargs={'pk': inventory.pk})
    assert app.get(url, status=302)


def test_non_staff_should_not_access_inventory_detail_page(loggedapp):
    inventory = InventoryFactory()
    url = reverse('monitoring:inventory', kwargs={'pk': inventory.pk})
    assert loggedapp.get(url, status=302)


def test_staff_should_access_inventory_detail_page(staffapp):
    inventory = InventoryFactory()
    url = reverse('monitoring:inventory', kwargs={'pk': inventory.pk})
    assert staffapp.get(url, status=200)


def test_staff_can_create_inventoryspeciment_by_barcode(staffapp):
    inventory = InventoryFactory()
    specimen = SpecimenFactory()
    assert not InventorySpecimen.objects.filter(inventory=inventory,
                                                specimen=specimen)
    url = reverse('monitoring:inventory', kwargs={'pk': inventory.pk})
    form = staffapp.get(url).forms['by_barcode']
    form['specimen'] = specimen.barcode
    form.submit().follow()
    assert InventorySpecimen.objects.get(inventory=inventory,
                                         specimen=specimen)


def test_staff_can_create_inventoryspeciment_by_click_on_add_link(staffapp):
    inventory = InventoryFactory()
    specimen = SpecimenFactory(count=3)
    assert not InventorySpecimen.objects.filter(inventory=inventory,
                                                specimen=specimen)
    url = reverse('monitoring:inventory', kwargs={'pk': inventory.pk})
    resp = staffapp.get(url)
    redirect = resp.click(href=reverse('monitoring:inventoryspecimen_add',
                                       kwargs={
                                            'inventory_pk': inventory.pk,
                                            'specimen_pk': specimen.pk}))
    assert redirect.location.endswith(url)
    assert InventorySpecimen.objects.get(inventory=inventory,
                                         specimen=specimen)
    assert InventorySpecimen.objects.get(inventory=inventory,
                                         specimen=specimen).count == 3


def test_staff_can_remove_inventoryspeciment_by_click_on_remove_link(staffapp):
    inventory = InventoryFactory()
    specimen = SpecimenFactory()
    InventorySpecimen.objects.create(inventory=inventory,
                                     specimen=specimen)
    url = reverse('monitoring:inventory', kwargs={'pk': inventory.pk})
    resp = staffapp.get(url)
    redirect = resp.click(href=reverse('monitoring:inventoryspecimen_remove',
                                       kwargs={
                                            'inventory_pk': inventory.pk,
                                            'specimen_pk': specimen.pk}))
    assert redirect.location.endswith(url)
    assert not InventorySpecimen.objects.filter(inventory=inventory,
                                                specimen=specimen)


def test_can_increase_inventoryspeciment_by_click_on_increase_link(staffapp):
    inventory = InventoryFactory()
    specimen = SpecimenFactory()
    m2m = InventorySpecimen.objects.create(inventory=inventory,
                                           specimen=specimen,
                                           count=2)
    url = reverse('monitoring:inventory', kwargs={'pk': inventory.pk})
    resp = staffapp.get(url)
    redirect = resp.click(href=reverse('monitoring:inventoryspecimen_increase',
                                       kwargs={'pk': m2m.pk}))
    assert redirect.location.endswith(url)
    assert InventorySpecimen.objects.get(inventory=inventory,
                                         specimen=specimen).count == 3


def test_can_decrease_inventoryspeciment_by_click_on_decrease_link(staffapp):
    inventory = InventoryFactory()
    specimen = SpecimenFactory()
    m2m = InventorySpecimen.objects.create(inventory=inventory,
                                           specimen=specimen,
                                           count=2)
    url = reverse('monitoring:inventory', kwargs={'pk': inventory.pk})
    resp = staffapp.get(url)
    redirect = resp.click(href=reverse('monitoring:inventoryspecimen_decrease',
                                       kwargs={'pk': m2m.pk}))
    assert redirect.location.endswith(url)
    assert InventorySpecimen.objects.get(inventory=inventory,
                                         specimen=specimen).count == 1