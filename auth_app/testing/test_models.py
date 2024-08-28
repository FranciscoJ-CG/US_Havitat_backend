import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from auth_app.models import UserType, DocumentType, User

@pytest.fixture
def user_type():
    return UserType.objects.create(name="Test User Type")

@pytest.fixture
def document_type():
    return DocumentType.objects.create(name="Test Document Type")

@pytest.fixture
def user(user_type, document_type):
    return User.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password="testpass123",
        type=user_type,
        document=12345678,
        document_type=document_type,
        worker=False
    )

@pytest.fixture
def group():
    return Group.objects.create(name="Test Group")

@pytest.fixture
def permission():
    content_type = ContentType.objects.get_for_model(User)
    return Permission.objects.create(
        codename="test_permission",
        name="Test Permission",
        content_type=content_type,
    )

@pytest.mark.django_db
class TestUserType:
    def test_create_user_type(self, user_type):
        assert user_type.name == "Test User Type"

    def test_str_representation(self, user_type):
        assert str(user_type) == "Test User Type"

    @pytest.mark.parametrize("name", [
        "",
        "A" * 256,  # Exceeds max_length
    ])
    def test_invalid_name(self, name):
        with pytest.raises(ValidationError):
            UserType.objects.create(name=name).full_clean()

    def test_verbose_name(self):
        assert UserType._meta.verbose_name == "Tipo de Usuario"
        assert UserType._meta.verbose_name_plural == "Tipos de Usuarios"

@pytest.mark.django_db
class TestDocumentType:
    def test_create_document_type(self, document_type):
        assert document_type.name == "Test Document Type"

    def test_str_representation(self, document_type):
        assert str(document_type) == "Test Document Type"

    @pytest.mark.parametrize("name", [
        "",
        "A" * 256,  # Exceeds max_length
    ])
    def test_invalid_name(self, name):
        with pytest.raises(ValidationError):
            DocumentType.objects.create(name=name).full_clean()

    def test_verbose_name(self):
        assert DocumentType._meta.verbose_name == "Tipo de Documento"
        assert DocumentType._meta.verbose_name_plural == "Tipos de Documentos"

@pytest.mark.django_db
class TestUser:
    def test_create_user(self, user, user_type, document_type):
        assert user.username == "testuser"
        assert user.email == "testuser@example.com"
        assert user.type == user_type
        assert user.document == 12345678
        assert user.document_type == document_type
        assert user.worker is False

    def test_str_representation(self, user):
        assert str(user) == "testuser"

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123"
        )
        assert superuser.is_superuser
        assert superuser.is_staff

    @pytest.mark.parametrize("field,value", [
        ("username", ""),
        ("username", "a" * 151),  # Exceeds max_length
        ("email", "invalid_email"),
        ("document", "not_an_integer"),
    ])
    def test_invalid_fields(self, user, field, value):
        setattr(user, field, value)
        with pytest.raises(ValidationError):
            user.full_clean()

    def test_worker_default(self):
        user = User.objects.create_user(username="worker_test")
        assert user.worker is False

    def test_optional_fields(self):
        user = User.objects.create_user(username="optional_test")
        assert user.type is None
        assert user.document is None
        assert user.document_type is None

    def test_verbose_name(self):
        assert User._meta.verbose_name == "Usuario"
        assert User._meta.verbose_name_plural == "Usuarios"

@pytest.mark.django_db
class TestUserRelationships:
    def test_user_groups(self, user, group):
        user.groups.add(group)
        assert group in user.groups.all()

    def test_user_permissions(self, user, permission):
        user.user_permissions.add(permission)
        assert permission in user.user_permissions.all()

    def test_related_name_groups(self, user, group):
        user.groups.add(group)
        assert user in group.auth_app_users.all()

    def test_related_name_permissions(self, user, permission):
        user.user_permissions.add(permission)
        assert user in permission.auth_app_users.all()

@pytest.mark.django_db
class TestEdgeCases:
    def test_create_user_without_username(self):
        with pytest.raises(ValueError):
            User.objects.create_user(username="")

    def test_user_with_same_document(self, user, document_type):
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="another_user",
                document=user.document,
                document_type=document_type
            )

    def test_user_type_cascade_delete(self, user):
        with pytest.raises(IntegrityError):
            user_type = user.type
            user_type.delete()
        user.refresh_from_db()

    def test_document_type_cascade_delete(self, user):
        with pytest.raises(IntegrityError):
            document_type = user.document_type
            document_type.delete()
        user.refresh_from_db()

    def test_user_with_many_groups(self, user):
        groups = [Group.objects.create(name=f"Group {i}") for i in range(100)]
        user.groups.set(groups)
        assert user.groups.count() == 100

    def test_user_with_many_permissions(self, user):
        content_type = ContentType.objects.get_for_model(User)
        permissions = [
            Permission.objects.create(
                codename=f"perm_{i}",
                name=f"Permission {i}",
                content_type=content_type
            ) for i in range(100)
        ]
        user.user_permissions.set(permissions)
        assert user.user_permissions.count() == 100
