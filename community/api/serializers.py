from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from community.models import ProductAnswer, ProductQuestion, ProductReview
from community.services.answer_service import AnswerService
from community.services.question_service import QuestionService
from community.services.review_service import ReviewService


# =========================================================
# Helpers
# =========================================================

def get_public_user_name(user):
    """
    نام عمومی کاربر برای نمایش در سایت.

    username عمداً نمایش داده نمی‌شود چون در بازبیا
    ممکن است username همان شماره موبایل کاربر باشد.
    """

    first_name = (getattr(user, "first_name", "") or "").strip()

    if first_name:
        return first_name

    return "کاربر بازبیا"


def raise_drf_validation_error(exc):
    """
    تبدیل ValidationError جنگو به ValidationError مربوط به DRF.
    """

    if hasattr(exc, "messages"):
        raise serializers.ValidationError(exc.messages)

    raise serializers.ValidationError(str(exc))


# =========================================================
# Product Answer
# =========================================================

class ProductAnswerSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    helpful_count = serializers.SerializerMethodField()
    user_found_helpful = serializers.SerializerMethodField()

    question_id = serializers.IntegerField(source="question.id", read_only=True)

    class Meta:
        model = ProductAnswer

        fields = [
            "id",
            "question_id",
            "user_name",
            "body",
            "is_verified_purchase",
            "is_official",
            "helpful_count",
            "user_found_helpful",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "question_id",
            "user_name",
            "is_verified_purchase",
            "is_official",
            "helpful_count",
            "user_found_helpful",
            "status",
            "created_at",
            "updated_at",
        ]

    def get_user_name(self, obj):
        return get_public_user_name(obj.user)

    def get_helpful_count(self, obj):
        return obj.helpful_votes.count()

    def get_user_found_helpful(self, obj):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return False

        return obj.helpful_votes.filter(user=request.user).exists()

    def validate_body(self, value):
        value = (value or "").strip()

        if not value:
            raise serializers.ValidationError("متن پاسخ نمی‌تواند خالی باشد.")

        return value

    def create(self, validated_data):
        request = self.context.get("request")
        question = self.context.get("question")

        if request is None:
            raise serializers.ValidationError("اطلاعات درخواست در دسترس نیست.")

        if question is None:
            raise serializers.ValidationError("پرسش مشخص نشده است.")

        try:
            return AnswerService.create_answer(
                user=request.user,
                question=question,
                body=validated_data["body"],
            )

        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)


# =========================================================
# Product Question
# =========================================================

class ProductQuestionSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    answers = serializers.SerializerMethodField()
    answer_count = serializers.SerializerMethodField()

    product_id = serializers.IntegerField(source="product.id", read_only=True)

    class Meta:
        model = ProductQuestion

        fields = [
            "id",
            "product_id",
            "user_name",
            "body",
            "status",
            "answers",
            "answer_count",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "product_id",
            "user_name",
            "status",
            "answers",
            "answer_count",
            "created_at",
            "updated_at",
        ]

    def get_user_name(self, obj):
        return get_public_user_name(obj.user)

    def get_answers(self, obj):
        answers = (
            obj.answers
            .filter(status=ProductAnswer.STATUS_APPROVED)
            .select_related("user")
            .order_by(
                "-is_official",
                "-is_verified_purchase",
                "created_at",
            )
        )

        return ProductAnswerSerializer(
            answers,
            many=True,
            context=self.context,
        ).data

    def get_answer_count(self, obj):
        return obj.answers.filter(status=ProductAnswer.STATUS_APPROVED).count()

    def validate_body(self, value):
        value = (value or "").strip()

        if not value:
            raise serializers.ValidationError("متن پرسش نمی‌تواند خالی باشد.")

        return value

    def create(self, validated_data):
        request = self.context.get("request")
        product = self.context.get("product")

        if request is None:
            raise serializers.ValidationError("اطلاعات درخواست در دسترس نیست.")

        if product is None:
            raise serializers.ValidationError("محصول مشخص نشده است.")

        try:
            return QuestionService.create_question(
                user=request.user,
                product=product,
                body=validated_data["body"],
            )

        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)


# =========================================================
# Product Review
# =========================================================

class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    helpful_count = serializers.SerializerMethodField()
    user_found_helpful = serializers.SerializerMethodField()

    product_id = serializers.IntegerField(source="product.id", read_only=True)

    class Meta:
        model = ProductReview

        fields = [
            "id",
            "product_id",
            "user_name",
            "rating",
            "title",
            "body",
            "is_verified_purchase",
            "helpful_count",
            "user_found_helpful",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "product_id",
            "user_name",
            "is_verified_purchase",
            "helpful_count",
            "user_found_helpful",
            "status",
            "created_at",
            "updated_at",
        ]

    def get_user_name(self, obj):
        return get_public_user_name(obj.user)

    def get_helpful_count(self, obj):
        return obj.helpful_votes.count()

    def get_user_found_helpful(self, obj):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return False

        return obj.helpful_votes.filter(user=request.user).exists()

    def validate_title(self, value):
        return (value or "").strip()

    def validate_body(self, value):
        value = (value or "").strip()

        if not value:
            raise serializers.ValidationError("متن دیدگاه نمی‌تواند خالی باشد.")

        return value

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("امتیاز باید بین ۱ تا ۵ باشد.")

        return value

    def create(self, validated_data):
        request = self.context.get("request")
        product = self.context.get("product")

        if request is None:
            raise serializers.ValidationError("اطلاعات درخواست در دسترس نیست.")

        if product is None:
            raise serializers.ValidationError("محصول مشخص نشده است.")

        try:
            return ReviewService.create_review(
                user=request.user,
                product=product,
                rating=validated_data["rating"],
                title=validated_data.get("title", ""),
                body=validated_data["body"],
            )

        except DjangoValidationError as exc:
            raise_drf_validation_error(exc)