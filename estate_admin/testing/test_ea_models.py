# estate_admin/testing/test_models.py
import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from estate_admin.models import (
    SuperUnit, ComplexType, Complex, UnitType, Unit, AdminBalance,
    DynamicRole, Relationship
)
from auth_app.models import User

@pytest.fixture
def super_unit():
    return SuperUnit.objects.create(name="Test Super Unit")

@pytest.fixture
def complex_type():
    return ComplexType.objects.create(name="Test Complex Type")

@pytest.fixture
def complex(super_unit, complex_type):
    return Complex.objects.create(
        name="Test Complex",
        type=complex_type,
        super_unit=super_unit
    )

@pytest.fixture
def unit_type():
    return UnitType.objects.create(name="Test Unit Type")

@pytest.fixture
def unit(complex, unit_type):
    return Unit.objects.create(
        complex=complex,
        type=unit_type,
        name="Test Unit"
    )

@pytest.fixture
def user():
    return User.objects.create(username="testuser")

@pytest.fixture
def worker_user():
    return User.objects.create(username="worker", worker=True)

@pytest.mark.django_db
class TestSuperUnit:
    def test_create_super_unit(self, super_unit):
        assert super_unit.name == "Test Super Unit"
        assert super_unit.created_at is not None

    @pytest.mark.parametrize("name", [
        "",
        "A" * 256,  # Exceeds max_length
        None,
    ])
    def test_invalid_super_unit_name(self, name):
        super_unit = SuperUnit(name=name)
        with pytest.raises(ValidationError):
            super_unit.full_clean()

    def test_str_representation(self, super_unit):
        assert str(super_unit) == "Test Super Unit"

@pytest.mark.django_db
class TestComplexType:
    def test_create_complex_type(self, complex_type):
        assert complex_type.name == "Test Complex Type"

    @pytest.mark.parametrize("name", [
        "",
        "A" * 256,  # Exceeds max_length
        None,
    ])
    def test_invalid_complex_type_name(self, name):
        complex_type = ComplexType(name=name)
        with pytest.raises(ValidationError):
            complex_type.full_clean()

    def test_str_representation(self, complex_type):
        assert str(complex_type) == "Test Complex Type"

@pytest.mark.django_db
class TestComplex:
    def test_create_complex(self, complex, complex_type, super_unit):
        assert complex.name == "Test Complex"
        assert complex.type == complex_type
        assert complex.super_unit == super_unit
        assert complex.created_at is not None

    @pytest.mark.parametrize("name", [
        "",
        "A" * 256,  # Exceeds max_length
        None,
    ])
    def test_invalid_complex_name(self, name, complex_type, super_unit):
        complex = Complex(name=name, type=complex_type, super_unit=super_unit)
        with pytest.raises(ValidationError):
            complex.full_clean()

    def test_str_representation(self, complex):
        assert str(complex) == f"Test Complex -- Test Super Unit"

    def test_bank_id_optional(self, complex_type, super_unit, user):
        complex = Complex.objects.create(
            name="Complex with Bank",
            type=complex_type,
            super_unit=super_unit,
            bank_id=user
        )
        assert complex.bank_id == user

@pytest.mark.django_db
class TestUnitType:
    def test_create_unit_type(self, unit_type):
        assert unit_type.name == "Test Unit Type"

    @pytest.mark.parametrize("name", [
        "",
        "A" * 256,  # Exceeds max_length
        None,
    ])
    def test_invalid_unit_type_name(self, name):
        unit_type = UnitType(name=name)
        with pytest.raises(ValidationError):
            unit_type.full_clean()

    def test_str_representation(self, unit_type):
        assert str(unit_type) == "Test Unit Type"

@pytest.mark.django_db
class TestUnit:
    def test_create_unit(self, unit, complex, unit_type):
        assert unit.name == "Test Unit"
        assert unit.complex == complex
        assert unit.type == unit_type
        assert unit.created_at is not None

    @pytest.mark.parametrize("name", [
        "",
        "A" * 256,  # Exceeds max_length
        None,
    ])
    def test_invalid_unit_name(self, name, complex, unit_type):
        unit = Unit(name=name, complex=complex, type=unit_type)
        with pytest.raises(ValidationError):
            unit.full_clean()

    def test_str_representation(self, unit):
        assert str(unit) == "Test Unit"

    def test_unique_together_constraint(self, complex, unit_type):
        Unit.objects.create(name="Unique Unit", complex=complex, type=unit_type)
        with pytest.raises(IntegrityError):
            Unit.objects.create(name="Unique Unit", complex=complex, type=unit_type)

    def test_optional_comment(self, complex, unit_type):
        unit = Unit.objects.create(
            name="Unit with Comment",
            complex=complex,
            type=unit_type,
            comment="This is a test comment"
        )
        assert unit.comment == "This is a test comment"

@pytest.mark.django_db
class TestAdminBalance:
    def test_create_admin_balance(self, unit):
        admin_balance = AdminBalance.objects.create(
            unit=unit,
            balance=1000
        )
        assert admin_balance.unit == unit
        assert admin_balance.balance == 1000
        assert admin_balance.last_updated is not None

    def test_str_representation(self, unit):
        admin_balance = AdminBalance.objects.create(unit=unit, balance=1000)
        assert str(admin_balance) == f"Test Unit - Balance: 1000"

    @pytest.mark.parametrize("balance", [
        -1000,  # Negative balance
        1000000000,  # Very large balance
        0,  # Zero balance
    ])
    def test_various_balances(self, unit, balance):
        admin_balance = AdminBalance.objects.create(unit=unit, balance=balance)
        assert admin_balance.balance == balance

@pytest.mark.django_db
class TestDynamicRole:
    def test_create_dynamic_role(self):
        dynamic_role = DynamicRole.objects.create(name="Test Dynamic Role")
        assert dynamic_role.name == "Test Dynamic Role"

    def test_str_representation(self):
        dynamic_role = DynamicRole.objects.create(name="Custom Role")
        assert str(dynamic_role) == "Custom Role"

    def test_unique_name_constraint(self):
        DynamicRole.objects.create(name="Unique Role")
        with pytest.raises(IntegrityError):
            DynamicRole.objects.create(name="Unique Role")

@pytest.mark.django_db
class TestRelationship:
    @pytest.mark.parametrize("role,permission_level", [
        ('owner', 'read'),
        ('leaser', 'write'),
        ('agent', 'admin'),
        ('possessor', 'read'),
        ('estate_admin', 'admin'),
        ('other', 'write'),
    ])
    def test_create_relationship(self, user, complex, role, permission_level):
        if role == 'estate_admin':
            user.worker = True
            user.save()
        
        relationship = Relationship(user=user, complex=complex, role=role, permission_level=permission_level)
        
        if role == 'estate_admin' and not user.worker:
            with pytest.raises(ValidationError):
                relationship.full_clean()
        else:
            relationship.full_clean()
            relationship.save()
            assert relationship.user == user
            assert relationship.complex == complex
            assert relationship.role == role
            assert relationship.permission_level == permission_level

    def test_relationship_constraints(self, user, unit, complex, super_unit):
        # Test that a relationship must be associated with exactly one of unit, complex, or super_unit
        with pytest.raises(ValidationError):
            relationship = Relationship(user=user, role='owner', permission_level='read')
            relationship.full_clean()
            relationship.save()
        
        with pytest.raises(ValidationError):
            relationship = Relationship(user=user, unit=unit, complex=complex, role='owner', permission_level='read')
            relationship.full_clean()
            relationship.save()

        # Test estate_admin constraints
        with pytest.raises(ValidationError):
            relationship = Relationship(user=user, unit=unit, role='estate_admin', permission_level='admin')
            relationship.full_clean()
            relationship.save()

        # Create a worker user
        worker_user = User.objects.create(username="worker", worker=True)
        
        # This should work
        estate_admin_relationship = Relationship(user=worker_user, super_unit=super_unit, role='estate_admin', permission_level='admin')
        estate_admin_relationship.full_clean()
        estate_admin_relationship.save()
        assert estate_admin_relationship.user.is_staff == True

        # Test that a user with estate_admin role cannot have other relationships
        with pytest.raises(ValidationError):
            relationship = Relationship(user=worker_user, unit=unit, role='owner', permission_level='read')
            relationship.full_clean()
            relationship.save()

    def test_other_role(self, user, complex):
        dynamic_role = DynamicRole.objects.create(name="Custom Role")
        relationship = Relationship(user=user, complex=complex, role='other', other_role=dynamic_role, permission_level='read')
        relationship.full_clean()
        relationship.save()
        assert relationship.other_role == dynamic_role

        # Test that other_role is set to None if role is not 'other'
        relationship.role = 'owner'
        relationship.full_clean()
        relationship.save()
        relationship.refresh_from_db()
        assert relationship.other_role is None


    def test__unique_together_constraint(self, user, unit):
        # Create the initial relationship
        Relationship.objects.create(
            user=user,
            unit=unit,
            role='owner',
            permission_level='read'
        )

        # Attempt to create a duplicate relationship
        with pytest.raises(IntegrityError):
            duplicate_relationship = Relationship(
                user=user,
                unit=unit,
                role='owner',
                permission_level='read'
            )
            duplicate_relationship.save()



    @pytest.mark.parametrize("invalid_role", [
        'invalid_role',
        '',
        None,
    ])
    def test_invalid_role(self, user, complex, invalid_role):
        relationship = Relationship(user=user, complex=complex, role=invalid_role, permission_level='read')
        with pytest.raises(ValidationError):
            relationship.full_clean()

    @pytest.mark.parametrize("invalid_permission", [
        'invalid_permission',
        '',
        None,
    ])
    def test_invalid_permission_level(self, user, complex, invalid_permission):
        relationship = Relationship(user=user, complex=complex, role='owner', permission_level=invalid_permission)
        with pytest.raises(ValidationError):
            relationship.full_clean()
