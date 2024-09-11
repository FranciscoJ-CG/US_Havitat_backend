# estate_admin/tests/test_models.py
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

import pytest

from estate_admin.models import (
    Havitat,
    ComplexType,
    UnitType,
    DynamicRole,
)

from .factories import (
    ComplexFactory,
    UnitFactory,
    RelationshipFactory,
    ComplexTypeFactory,
    HavitatFactory,
    UnitTypeFactory,
    DynamicRoleFactory,
)
from auth_app.tests.factories import UserFactory


@pytest.mark.django_db
class TestHavitatModel:
    def test_create_havitat(self):
        havitat = Havitat.objects.create(name="Test Havitat")
        assert havitat.name == "Test Havitat"
        assert str(havitat) == "Test Havitat"

@pytest.mark.django_db
class TestComplexTypeModel:
    def test_create_complex_type(self):
        complex_type = ComplexType.objects.create(name="Residential")
        assert complex_type.name == "Residential"
        assert str(complex_type) == "Residential"

@pytest.mark.django_db
class TestUnitTypeModel:
    def test_create_unit_type(self):
        unit_type = UnitType.objects.create(name="Apartment")
        assert unit_type.name == "Apartment"
        assert str(unit_type) == "Apartment"

@pytest.mark.django_db
class TestDynamicRoleModel:
    def test_create_dynamic_role(self):
        dynamic_role = DynamicRole.objects.create(name="Manager")
        assert dynamic_role.name == "Manager"
        assert str(dynamic_role) == "Manager"


@pytest.mark.django_db
class TestComplexModel:
    def test_create_complex(self):
        complex_instance = ComplexFactory()
        assert complex_instance.name is not None
        assert str(complex_instance) == f"{complex_instance.name} -- {complex_instance.havitat.name}"

    def test_complex_type_relation(self):
        complex_type = ComplexTypeFactory(name="Commercial")
        complex_instance = ComplexFactory(type=complex_type)
        assert complex_instance.type.name == "Commercial"
        assert complex_instance.type == complex_type

    def test_havitat_relation(self):
        havitat = HavitatFactory(name="Green Valley")
        complex_instance = ComplexFactory(havitat=havitat)
        assert complex_instance.havitat.name == "Green Valley"
        assert complex_instance.havitat == havitat

@pytest.mark.django_db
class TestUnitModel:
    def test_create_unit(self):
        unit = UnitFactory()
        assert unit.name is not None
        assert str(unit) == unit.name

    def test_unique_together_constraint(self):
        unit = UnitFactory()
        with pytest.raises(IntegrityError):
            UnitFactory(name=unit.name, complex=unit.complex)

    def test_unit_complex_relation(self):
        complex_instance = ComplexFactory(name="Skyline Towers")
        unit = UnitFactory(complex=complex_instance)
        assert unit.complex.name == "Skyline Towers"
        assert unit.complex == complex_instance

    def test_unit_type_relation(self):
        unit_type_instance = UnitTypeFactory(name="Penthouse")
        unit = UnitFactory(type=unit_type_instance)
        assert unit.type.name == "Penthouse"
        assert unit.type == unit_type_instance

@pytest.mark.django_db
class TestRelationshipModel:
    def test_create_relationship(self):
        relationship = RelationshipFactory()
        assert relationship.role == "owner"
        assert relationship.permission_level == "admin"

    def test_only_one_of_unit_complex_havitat(self):
        # Invalid cases:
        with pytest.raises(ValidationError):
            RelationshipFactory(
                unit=UnitFactory(),
                complex=ComplexFactory(),
                havitat=HavitatFactory()
            )
        with pytest.raises(ValidationError):
            RelationshipFactory(
                unit=UnitFactory(),
                havitat=HavitatFactory()
            )
        with pytest.raises(ValidationError):
            RelationshipFactory(
                unit=UnitFactory(),
                complex=ComplexFactory(),
            )
        with pytest.raises(ValidationError):
            RelationshipFactory(
                complex=ComplexFactory(),
                havitat=HavitatFactory()
            )

        # Valid cases:
        relationship = RelationshipFactory(unit=UnitFactory(), complex=None, havitat=None)
        assert relationship.unit is not None
        assert relationship.complex is None
        assert relationship.havitat is None

        relationship = RelationshipFactory(unit=None, complex=ComplexFactory(), havitat=None)
        assert relationship.unit is None
        assert relationship.complex is not None
        assert relationship.havitat is None

        relationship = RelationshipFactory(unit=None, complex=None, havitat=HavitatFactory())
        assert relationship.unit is None
        assert relationship.complex is None
        assert relationship.havitat is not None

    def test_estate_admin_constraints(self):
        with pytest.raises(ValidationError):
            RelationshipFactory(role="estate_admin", unit=UnitFactory())

        user = UserFactory(worker=False)
        with pytest.raises(ValidationError):
            RelationshipFactory(role="estate_admin", user=user, unit=None)

        user = UserFactory(worker=True)
        relationship = RelationshipFactory(role="estate_admin", user=user, unit=None, complex=ComplexFactory())
        assert relationship.user.is_staff
        assert relationship.unit is None
        assert relationship.complex is not None

    def test_user_with_estate_admin_role_cannot_have_other_roles_with_unit(self):
        user = UserFactory(worker=True)
        RelationshipFactory(user=user, role="estate_admin", unit=None, complex=ComplexFactory())

        with pytest.raises(ValidationError):
            RelationshipFactory(user=user, role="owner", unit=UnitFactory())

    def test_other_role_field_constraints(self):
        with pytest.raises(ValidationError):
            RelationshipFactory(role="owner",  other_role=DynamicRoleFactory())

        dynamic_role = DynamicRoleFactory()
        relationship = RelationshipFactory(role="other", other_role=dynamic_role)
        assert relationship.other_role == dynamic_role


