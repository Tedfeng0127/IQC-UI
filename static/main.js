// $(document).raedy(function () {

//     $(".btn-div").click(function () {
//         $.ajax({
//             url:"/update_input_iqc_data_page",
//             type:"POST",
//             datatype:"json",
//             success:function (data) {
                
//             }
//         })
//     })
// });

function showInspectionBox() {
    var inspectionForm = document.getElementById("inspection_box");
    var supplierForm = document.getElementById("supplier_box");
    var queryForm = document.getElementById("query_box");
    var probationForm = document.getElementById("probation_box");
    inspectionForm.style.display = "";
    supplierForm.style.display = "none";
    queryForm.style.display = "none";
    probationForm.style.display = "none";
}

function showSupplierBox() {
    var inspectionForm = document.getElementById("inspection_box");
    var supplierForm = document.getElementById("supplier_box");
    var queryForm = document.getElementById("query_box");
    var probationForm = document.getElementById("probation_box");
    inspectionForm.style.display = "none";
    supplierForm.style.display = "";
    queryForm.style.display = "none";
    probationForm.style.display = "none";
}

function showQueryBox() {
    var inspectionForm = document.getElementById("inspection_box");
    var supplierForm = document.getElementById("supplier_box");
    var queryForm = document.getElementById("query_box");
    var probationForm = document.getElementById("probation_box");
    inspectionForm.style.display = "none";
    supplierForm.style.display = "none";
    queryForm.style.display = "";
    probationForm.style.display = "none";
}

function showProbationBox() {
    var inspectionForm = document.getElementById("inspection_box");
    var supplierForm = document.getElementById("supplier_box");
    var queryForm = document.getElementById("query_box");
    var probationForm = document.getElementById("probation_box");
    inspectionForm.style.display = "none";
    supplierForm.style.display = "none";
    queryForm.style.display = "none";
    probationForm.style.display = "";
}