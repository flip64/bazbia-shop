```javascript
$(document).ready(function () {
    const persianLanguage = {
        decimal: "",
        emptyTable: "اطلاعاتی برای نمایش وجود ندارد",
        info: "نمایش _START_ تا _END_ از مجموع _TOTAL_ مورد",
        infoEmpty: "نمایش ۰ تا ۰ از مجموع ۰ مورد",
        infoFiltered: "(فیلترشده از مجموع _MAX_ مورد)",
        infoPostFix: "",
        thousands: ",",
        lengthMenu: "نمایش _MENU_ مورد",
        loadingRecords: "در حال بارگذاری...",
        processing: "در حال پردازش...",
        search: "جستجو:",
        searchPlaceholder: "جستجو در جدول",
        zeroRecords: "موردی مطابق جستجو پیدا نشد",

        paginate: {
            first: "اول",
            last: "آخر",
            next: '<i class="ion-chevron-left"></i>',
            previous: '<i class="ion-chevron-right"></i>',
        },

        aria: {
            sortAscending: ": فعال‌سازی مرتب‌سازی صعودی",
            sortDescending: ": فعال‌سازی مرتب‌سازی نزولی",
        },

        buttons: {
            copy: "کپی",
            csv: "CSV",
            excel: "اکسل",
            pdf: "PDF",
            print: "چاپ",
            copyTitle: "کپی اطلاعات",
            copySuccess: {
                _: "%d ردیف کپی شد",
                1: "یک ردیف کپی شد",
            },
        },
    };


    /*
     * جدول معمولی
     */
    $(".data-table").DataTable({
        scrollCollapse: true,
        autoWidth: false,
        responsive: true,

        columnDefs: [
            {
                targets: "datatable-nosort",
                orderable: false,
            },
        ],

        lengthMenu: [
            [10, 25, 50, -1],
            [10, 25, 50, "همه"],
        ],

        language: persianLanguage,
    });


    /*
     * جدول دارای خروجی
     */
    $(".data-table-export").DataTable({
        scrollCollapse: true,
        autoWidth: false,
        responsive: true,

        columnDefs: [
            {
                targets: "datatable-nosort",
                orderable: false,
            },
        ],

        lengthMenu: [
            [10, 25, 50, -1],
            [10, 25, 50, "همه"],
        ],

        language: persianLanguage,

        /*
         * B = دکمه‌های خروجی
         * l = تعداد ردیف‌ها
         * f = جستجو
         * r = وضعیت پردازش
         * t = جدول
         * i = اطلاعات جدول
         * p = صفحه‌بندی
         */
        dom: "Blfrtip",

        buttons: [
            {
                extend: "copy",
                text: "کپی",
            },
            {
                extend: "csv",
                text: "CSV",
            },
            {
                extend: "pdf",
                text: "PDF",
            },
            {
                extend: "print",
                text: "چاپ",
            },
        ],
    });


    /*
     * انتخاب یک ردیف
     */
    const selectRowTable = $(".select-row").DataTable();

    $(".select-row tbody").on("click", "tr", function () {
        if ($(this).hasClass("selected")) {
            $(this).removeClass("selected");
        } else {
            selectRowTable.$("tr.selected").removeClass("selected");
            $(this).addClass("selected");
        }
    });


    /*
     * انتخاب چند ردیف
     *
     * اگر جدول قبلاً با کلاس data-table-export ساخته شده باشد،
     * DataTable همان نمونه موجود را برمی‌گرداند.
     */
    $(".multiple-select-row").DataTable();

    $(".multiple-select-row tbody").on("click", "tr", function () {
        $(this).toggleClass("selected");
    });


    /*
     * جدول دارای Checkbox
     */
    const checkboxTable = $(".checkbox-datatable").DataTable({
        scrollCollapse: true,
        autoWidth: false,
        responsive: true,

        lengthMenu: [
            [10, 25, 50, -1],
            [10, 25, 50, "همه"],
        ],

        language: persianLanguage,

        columnDefs: [
            {
                targets: 0,
                searchable: false,
                orderable: false,
                className: "dt-body-center",

                render: function (data) {
                    const value = $("<div/>").text(data).html();

                    return `
                        <div class="dt-checkbox">
                            <input
                                type="checkbox"
                                name="id[]"
                                value="${value}"
                            >
                            <span class="dt-checkbox-label"></span>
                        </div>
                    `;
                },
            },
        ],

        order: [[1, "asc"]],
    });


    /*
     * انتخاب تمام Checkboxها
     */
    $("#example-select-all").on("click", function () {
        const rows = checkboxTable
            .rows({
                search: "applied",
            })
            .nodes();

        $('input[type="checkbox"]', rows).prop(
            "checked",
            this.checked
        );
    });


    /*
     * مدیریت حالت نیمه‌انتخاب‌شده Checkbox اصلی
     */
    $(".checkbox-datatable tbody").on(
        "change",
        'input[type="checkbox"]',
        function () {
            if (!this.checked) {
                const selectAllCheckbox =
                    $("#example-select-all").get(0);

                if (
                    selectAllCheckbox &&
                    selectAllCheckbox.checked &&
                    "indeterminate" in selectAllCheckbox
                ) {
                    selectAllCheckbox.indeterminate = true;
                }
            }
        }
    );
});
```

