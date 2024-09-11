# estate_admin/tests/factories.py
import factory
from auth_app.tests.factories import UserFactory
from estate_admin.models import (
    Havitat, ComplexType, Complex, UnitType, Unit, DynamicRole, Relationship
)

class HavitatFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Havitat

    name = factory.Faker('company')

class ComplexTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ComplexType

    name = factory.Faker('word')

class ComplexFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Complex

    name = factory.Faker('word')
    type = factory.SubFactory(ComplexTypeFactory)
    havitat = factory.SubFactory(HavitatFactory)

class UnitTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UnitType

    name = factory.Faker('word')

class UnitFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Unit

    name = factory.Faker('word')
    complex = factory.SubFactory(ComplexFactory)
    type = factory.SubFactory(UnitTypeFactory)

class DynamicRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DynamicRole

    name = factory.Faker('word')

class RelationshipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Relationship

    user = factory.SubFactory(UserFactory)
    unit = factory.SubFactory(UnitFactory)
    role = 'owner'
    permission_level = 'admin'
