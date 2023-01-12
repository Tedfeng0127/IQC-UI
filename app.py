from flask import Flask, redirect, render_template, request, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from module_program import *
import os
import sys
import datetime
import pymssql



app = Flask(__name__)

# session
app.config["SECRET_KEY"] = os.urandom(12).hex()
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_CONNECTION_STRING"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# 定義Model，利用Model操作資料庫的資料
class Item(db.Model):
    __tablename__ = "item"
    part_number = db.Column(db.String(50), primary_key=True)
    description = db.Column(db.String(250))
    category = db.Column(db.String(20))
    inspection_standard = db.Column(db.String(10))

class Document(db.Model):
    __tablename__ = "document"
    inspection_standard = db.Column(db.String(10), primary_key=True)
    aql = db.Column(db.Integer)

class Supplier(db.Model):
    __tablename__ = "supplier"
    supplier_number = db.Column(db.String(20), primary_key=True)
    supplier_name = db.Column(db.String(600))
    city = db.Column(db.String(30))
    sampling_state = db.Column(db.Integer)
    accumulation_counts = db.Column(db.String(10))

class Prefix(db.Model):
    __tablename__ = "prefix"
    regex_part_number_prefix = db.Column(db.String(20), primary_key=True)
    inspection_standard = db.Column(db.String(10))

class Record(db.Model):
    __tablename__ = "record"
    record_id = db.Column(db.Integer, primary_key=True)
    sampling_state = db.Column(db.Integer)
    inspection_date = db.Column(db.Date)
    supplier_number = db.Column(db.String)
    inspection_lot = db.Column(db.String)
    inspection_type = db.Column(db.String)
    order = db.Column(db.String)
    purchasing = db.Column(db.String)
    part_number = db.Column(db.String)
    item_rev = db.Column(db.String)
    quantity = db.Column(db.Integer)
    inspection_quantity = db.Column(db.SmallInteger)
    major_accept = db.Column(db.SmallInteger)
    major_reject = db.Column(db.SmallInteger)
    minor_accept = db.Column(db.SmallInteger)
    minor_reject = db.Column(db.SmallInteger)
    product_recorded_quantity = db.Column(db.SmallInteger)
    product_serial_number = db.Column(db.String)
    visual_inspection_result = db.Column(db.String)
    visual_inspection_defect_classification = db.Column(db.String)
    visual_inspection_defect_description = db.Column(db.String)
    date_code = db.Column(db.String)
    electrical_function_inspection_result = db.Column(db.String)
    electrical_function_inspection_defect_classification = db.Column(db.String)
    electrical_function_inspection_defect_description = db.Column(db.String)
    electrical_function_inspection_value = db.Column(db.String)
    package_way = db.Column(db.String)
    package_inspection_result = db.Column(db.String)
    package_inspection_defect_classification = db.Column(db.String)
    package_inspection_defect_description = db.Column(db.String)
    remark = db.Column(db.String)
    inspection_result = db.Column(db.Boolean)
    hyper_link = db.Column(db.String)
    inspector = db.Column(db.String)
    manager = db.Column(db.String)

class Revise(db.Model):
    __tablename__ = "revise_sampling_state_event"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    supplier_number = db.Column(db.String)
    supplier_name = db.Column(db.String)
    inspector = db.Column(db.String)

class Reject(db.Model):
    __tablename__ = "inspection_free_vendor_reject_event"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    supplier_number = db.Column(db.String)

class Manually60DaysLog(db.Model):
    __tablename__ = "manually_60_days_probation_log_event"
    id = db.Column(db.Integer, primary_key=True)
    supplier_number = db.Column(db.String)
    supplier_name = db.Column(db.String)
    description = db.Column(db.String)
    inspector = db.Column(db.String)
    record_time = db.Column(db.DateTime)
    date = db.Column(db.Date)

class RequiredToFree(db.Model):
    __tablename__ = "inspection_required_to_inspection_free_event"
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime)
    supplier_number = db.Column(db.String)
    supplier_name = db.Column(db.String)



@app.route("/")
def home():
    """
    首頁：輸入檢驗紀錄、更改廠商抽樣狀態、查詢檢驗紀錄、觀察特定廠商60天
    """
    return render_template("index.html")


@app.route("/supplier", methods=["POST"])
def search_supplier():
    """
    利用供應商代碼搜尋供應商，回傳供應商資訊的頁面
    """
    supplier_number = request.form.get("supplier_number")
    query_supplier = Supplier.query.filter_by(supplier_number=supplier_number).first()
    if query_supplier is None:
        return_data = ["", "資料庫中查無此供應商代碼 This supplier number isn't in the Database"]
    else:
        supplier_name = query_supplier.supplier_name
        sampling_state_code = query_supplier.sampling_state
        sampling_state_dict = {
            -1:"免驗 inspection free", 0:"減量檢驗 loosened level",
            1:"正常檢驗 normal level", 2:"加嚴檢驗 tightened level"}
        sampling_state = sampling_state_dict[sampling_state_code]
        return_data = [supplier_number, supplier_name, sampling_state]
    return render_template("revise_supplier_status.html", data=return_data)


@app.route("/revise_complete", methods=["POST"])
def revise_complete():
    """
    送出供應商的修改之後回傳修改成功頁面
    """
    supplier_number = request.form.get("supplier_number")
    supplier_name = request.form.get("supplier_name")
    original_sampling_state = request.form.get("original_sampling_state")
    new_sampling_state_code = request.form.get("new_sampling_state")
    inspector = request.form.get("inspector")
    sampling_state_dict = {"-1":"免驗", "0":"減量檢驗", "1":"正常檢驗", "2":"加嚴檢驗"}
    new_sampling_state = sampling_state_dict[new_sampling_state_code]
    if original_sampling_state == new_sampling_state or original_sampling_state != "免驗 inspection free":
        pass    
    else:
        # 修改供應商抽樣狀態
        query_supplier = Supplier.query.filter_by(supplier_number=supplier_number).first()
        query_supplier.sampling_state = int(new_sampling_state_code)
        query_supplier.accumulation_counts = "0/0/0"
        # 修改紀錄存入revise_sampling_state_event table
        revise = Revise(
            date=datetime.date.today().strftime("%Y-%m-%d"),
            supplier_number=supplier_number,
            supplier_name=supplier_name,
            inspector=inspector
        )
        db.session.add(revise)
        db.session.commit()
    return render_template("revise_complete.html")


@app.route("/query", methods=["POST"])
def query_record():
    """
    根據輸入的起始日期和結束日期，查詢並顯示這段期間的所有進料檢驗紀錄
    """
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    query_record = Record.query.filter(Record.inspection_date.between(start_date, end_date))
    data = []
    for row in query_record:
        sampling_state = {None:"無抽樣狀態", -1:"免驗", 0:"減量", 1:"正常", 2:"加嚴"}[row.sampling_state]
        inspection_result = {True:"ACC", False:"REJ"}[row.inspection_result]
        supplier_number = row.supplier_number
        part_number = row.part_number
        query_supplier = Supplier.query.filter_by(supplier_number=supplier_number).first()
        query_item = Item.query.filter_by(part_number=part_number).first()
        supplier_name = query_supplier.supplier_name if query_supplier else "None"
        item_description = query_item.description if query_item else "None"
        data.append({
            "record_id":row.record_id,
            "inspection_date":str(row.inspection_date),
            "sampling_state":sampling_state,
            "supplier_number":supplier_number,
            "supplier_name":supplier_name,
            "inspection_lot":row.inspection_lot or "-",
            "inspection_type":row.inspection_type or "-",
            "order":row.order or "-",
            "purchasing":row.purchasing,
            "part_number":part_number,
            "item_description":item_description,
            "item_rev":row.item_rev or "-",
            "quantity":row.quantity,
            "inspection_quantity":row.inspection_quantity,
            "major_accept":0 if row.major_accept == 0 else row.major_accept or "-",
            "major_reject":0 if row.major_reject == 0 else row.major_reject or "-",
            "minor_accept":0 if row.minor_accept == 0 else row.minor_accept or "-",
            "minor_reject":0 if row.minor_reject == 0 else row.minor_reject or "-",
            "product_recorded_quantity":row.product_recorded_quantity or "-",
            "product_serial_number":row.product_serial_number or "-",
            "inspection_result":inspection_result,
            "visual_inspection_result":row.visual_inspection_result,
            "visual_inspection_defect_classification":row.visual_inspection_defect_classification or "-",
            "visual_inspection_defect_description":row.visual_inspection_defect_description or "-",
            "date_code":row.date_code or "-",
            "electrical_function_inspection_result":row.electrical_function_inspection_result,
            "electrical_function_inspection_defect_classification":row.electrical_function_inspection_defect_classification or "-",
            "electrical_function_inspection_defect_description":row.electrical_function_inspection_defect_description or "-",
            "electrical_function_inspection_value":row.electrical_function_inspection_value or "-",
            "package_inspection_result":row.package_inspection_result,
            "package_inspection_defect_classification":row.package_inspection_defect_classification or "-",
            "package_inspection_defect_description":row.package_inspection_defect_description or "-",
            "package_way":row.package_way or "-",
            "remark":row.remark or "-",
            "hyper_link":row.hyper_link or "-",
            "inspector":row.inspector,
            "manager":row.manager})
    return render_template("record_query_result.html", data=data)


@app.route("/probation", methods=["POST"])
def probation():
    """
    檢驗員在UI上手動輸入想要觀察60天的廠商，存入一筆紀錄到manually_60_days_probation_log_event table
    """
    supplier_number = request.form.get("supplier_number")
    description = request.form.get("description")
    inspector = request.form.get("inspector")
    current_time = datetime.datetime.now() + datetime.timedelta(hours=8)
    time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    date = (current_time + datetime.timedelta(days=60)).strftime("%Y-%m-%d")
    query_supplier = Supplier.query.filter_by(supplier_number=supplier_number).first()
    if not query_supplier:
        supplier_name = "None"
    else:
        supplier_name = query_supplier.supplier_name
    new_row = Manually60DaysLog(
        supplier_number=supplier_number,
        supplier_name=supplier_name,
        description=description,
        inspector=inspector,
        record_time=time,
        date=date
    )
    db.session.add(new_row)
    db.session.commit()
    return render_template("record_saved.html")


@app.route("/iqc_info_confirm", methods=["POST"])
def iqc_info_confirm():
    """
    回傳一個顯示前面輸入的檢驗紀錄資料的頁面，讓檢驗員確認輸入資料是否正確
    """
    try:
        iqc_info = request.form.get("iqc_info")
        data = split_input_iqc_info(iqc_info)
        # 刪除換行符號
        while ["\r"] in data:
            data.remove(["\r"])
        # 檢查輸入的欄位數
        column = set([len(d) for d in data])
        if column != {9}:
            return "請檢查輸入的欄位個數是否正確"

        # 抽樣狀態、檢驗量、主缺收退、次缺收退另外存
        additional_data = []

        # 判斷料號和廠商代號是不是新的，
        # 前端的jinja模板會根據這個判斷要不要把廠商代號和料號顯示成紅字
        conditional_data = []

        # 計算檢驗量 主缺 次缺
        for d in data:
            a_data = []
            quantity = int(float(d[-1].replace(",", "").replace(" ", "")))
            d[-1] = quantity
            part_number = d[5]
            supplier_number = d[0]
            query_item = Item.query.filter_by(part_number=part_number).first()
            query_supplier = Supplier.query.filter_by(supplier_number=supplier_number).first()
            
            # 輸入資料庫中沒有的新料號
            if query_item is None:
                prefix_table = Prefix.query.all()
                inspection_standard = generate_inspection_standard_of_new_part_number(prefix_table, part_number)
                query_document = Document.query.filter_by(inspection_standard=inspection_standard).first()
                sampling_method = query_document.aql if query_document is not None else 2
                aql = {0:"Major0.65 / Minor1.0", 1:"Major1.0 / Minor2.5", 2:"新料號無對應的前綴", None:"此檢驗規範無對應的抽樣計畫"}[sampling_method]
                no_item = True          # 前端的jinja模板根據這個變數判斷要不要把料號用紅字顯示
            else:
                inspection_standard = query_item.inspection_standard
                query_document = Document.query.filter_by(inspection_standard=inspection_standard).first()
                sampling_method = query_document.aql if query_document.aql is not None else 2
                aql = {0:"Major0.65 / Minor1.0", 1:"Major1.0 / Minor2.5", 2:"此檢驗規範無對應的抽樣計畫"}[sampling_method]
                no_item = False
            
            # 輸入資料庫中沒有的廠商代號
            if query_supplier is None:
                supplier_name = ""
                sampling_state = ""
                no_supplier = True   # 前端的jinja模板根據這個變數判斷要不要把廠商代號用紅字顯示
            else:
                supplier_name = query_supplier.supplier_name
                sampling_state_dict = {-1:"免驗", 0:"減量", 1:"正常", 2:"加嚴"}
                sampling_state = sampling_state_dict[query_supplier.sampling_state]
                no_supplier = False
            
            d.insert(0, supplier_name)
            d.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
            # 檢驗規範(根據料號取得)
            d.append(inspection_standard)
            # 抽樣計畫(根據檢驗規範取得)
            d.append(aql)
            # 抽樣狀態(根據廠商代號得知)
            a_data.append(sampling_state)
            a_data += calculate_inspection_quantity(quantity, sampling_method=sampling_method,\
                        sampling_state=sampling_state)
            additional_data.append(a_data)
            conditional_data.append((no_supplier, no_item))
        session["data"] = data
        session["conditional_data"] = conditional_data
        session["data_counts"] = len(data)
        session["click_counts"] = 0
        return render_template("info_confirm.html", rows=data, condition=conditional_data)
    # error message
    except Exception as e:
        return render_template("error_page.html", error_message=str(e))


@app.route("/input_iqc_data", methods=["GET", "POST"])
def input_iqc_data():
    """
    回傳讓檢驗員輸入檢驗紀錄的頁面
    """
    # 點擊"顯示下一筆檢驗紀錄"的按鈕
    if request.is_json:
        if len(session.get("data")) > 0:
            data = session.get("data").pop(0)
            conditional_data = session.get("conditional_data").pop(0)
            inspection_standard = data[-2]
            query_supplier = Supplier.query.filter_by(supplier_number=data[2]).first()
            query_item = Item.query.filter_by(part_number=data[7]).first()
            # 供應商代碼不在資料庫中，無法找到這間供應商的抽樣狀態
            if not query_supplier:
                sampling_state_number = -2
            else:
                sampling_state_number = query_supplier.sampling_state
            # 輸入的料號不在資料庫中，無法找到這個料適用的抽樣計畫
            if not query_item:
                # 如果是新料號，用檢驗規範判斷category應該是product或material
                if inspection_standard in ["QW-Q023", "QW-Q024", "QW-Q029"]:
                    category = "Product"
                    is_product = True
                else:
                    category = "Material"
                    is_product = False
            else:
                category = query_item.category
                # 判斷這個進料是不是成品
                is_product = True if category in ["Product", "STI SKU"] else False
            
            quantity = int(data[10])
            sampling_method_number = {"Major0.65 / Minor1.0":0, "Major1.0 / Minor2.5":1, "此檢驗規範無對應的抽樣計畫":2}[data[-1]]
            sampling_state = {-2:"", -1:"免驗", 0:"減量", 1:"正常", 2:"加嚴"}[sampling_state_number]
            # 如果進料是成品，只需要根據成品的邏輯計算檢驗量，不需要主缺 次缺
            if is_product:
                inspection_quantity = calculate_inspection_quantity_of_product(quantity=quantity)
            else:
                inspection_quantity = calculate_inspection_quantity(quantity,
                sampling_method=sampling_method_number, sampling_state=sampling_state)
            additional_data = [category, sampling_state] + inspection_quantity

            click_counts = session.get("click_counts")
            data_counts = session.get("data_counts")
            click_counts += 1
            return_dict = {
                "date":data[0],
                "supplier_name":data[1],
                "supplier_number":data[2],
                "inspection_lot":data[3],
                "inspection_type":data[4],
                "order":data[5],
                "purchasing":data[6],
                "part_number":data[7],
                "item_description":data[8],
                "item_rev":data[9],
                "quantity":data[10],
                "inspection_document":data[11],
                "aql":data[12],
                "category":additional_data[0],
                "sampling_state":additional_data[1],
                "inspection_quantity":additional_data[2],
                "major_accept":additional_data[3],
                "major_reject":additional_data[4],
                "minor_accept":additional_data[5],
                "minor_reject":additional_data[6],
                "click_counts":click_counts,
                "data_counts":data_counts,
                "no_supplier":conditional_data[0],
                "no_item":conditional_data[1],
                "is_product":is_product
            }
            return_json = jsonify(return_dict)
            session["click_counts"] = click_counts
            return return_json
    total_data_counts = session.get("data_counts")
    input_data_counts = total_data_counts - len(session.get("data"))
    return_data = [total_data_counts, input_data_counts]
    return render_template("input_iqc_record.html", return_data=return_data)


@app.route("/process_data", methods=["POST", "GET"])
def process_data():
    """
    處理前端輸入的資料，把資料寫入資料庫或做其他運算(Ex.計算抽樣狀態)
    """
    variable_names = [
        # 使用者輸入的資料
        "supplier_number", "inspection_lot", "inspection_type",
        "order", "purchasing", "part_number", "item_description", "quantity",
        # 根據使用者輸入的資料計算出的資料
        # 抽樣狀態、檢驗量、major收退、minor收退
        "sampling_state", "inspection_quantity",
        "major_accept", "major_reject", "minor_accept", "minor_reject",
        # 使用者填表單送出的資料
        "visual_inspection_result", "visual_inspection_defect_classification",
        "visual_inspection_defect_description", "date_code",
        "electrical_function_inspection_result", "electrical_function_inspection_defect_classification",
        "electrical_function_inspection_defect_description", "electrical_function_inspection_value",
        "package_inspection_result", "package_inspection_defect_classification",
        "package_inspection_defect_description", "package_way",
        "inspection_result", "item_rev", "category", "inspection_document",
        "product_recorded_quantity", "product_serial_number",
        "hyper_link", "remark", "inspector", "manager", "skip",
        # 隱藏在表單裡送出的資料
        "original_inspection_document", "original_category", "inspection_date", "aql",
        # 判斷這筆檢驗是不是成品
        "is_product"
    ]
    inspection_record = {variable:request.form.get(variable) for variable in variable_names}
    inspection_record["visual_inspection_defect_classification"] = request.form.getlist("visual_inspection_defect_classification")
    inspection_record["electrical_function_inspection_defect_classification"] = request.form.getlist("electrical_function_inspection_defect_classification")
    inspection_record["package_inspection_defect_classification"] = request.form.getlist("package_inspection_defect_classification")

    # 跳過此筆檢驗
    if inspection_record["skip"] == "true":
        pass
    # 取得檢驗紀錄資料，存入檢驗紀錄或修改資料庫    
    else:
        # 取得需要存進record table的資料，轉換資料格式(Ex.OK --> 1、NG --> 0)
        sampling_state = inspection_record["sampling_state"]  # 文字型態(免驗/減量/正常/加嚴)
        sampling_state = {"免驗":-1, "減量":0, "正常":1, "加嚴":2}[sampling_state]
        inspection_date = inspection_record["inspection_date"]
        supplier_number = inspection_record["supplier_number"]
        inspection_lot = inspection_record["inspection_lot"]
        inspection_lot = None if inspection_lot == "none" else inspection_lot
        inspection_type = inspection_record["inspection_type"]
        order = inspection_record["order"]
        order = None if order == "none" else order
        purchasing = inspection_record["purchasing"]
        purchasing = None if purchasing == "none" else purchasing
        part_number = inspection_record["part_number"]
        item_rev = inspection_record["item_rev"]
        quantity = int(inspection_record["quantity"])
        aql = {"Major0.65":0, "Major1.0":1, "此檢驗規範無對應的抽樣計畫":2}[inspection_record["aql"]]
        inspection_quantity = int(inspection_record["inspection_quantity"])
        major_accept = inspection_record["major_accept"]
        major_accept = None if major_accept == "none" else int(major_accept)
        major_reject = inspection_record["major_reject"]
        major_reject = None if major_reject == "none" else int(major_reject)
        minor_accept = inspection_record["minor_accept"]
        minor_accept = None if minor_accept == "none" else int(minor_accept)
        minor_reject = inspection_record["minor_reject"]
        minor_reject = None if minor_reject == "none" else int(minor_reject)
        product_recorded_quantity = inspection_record["product_recorded_quantity"]
        product_recorded_quantity = None if product_recorded_quantity == "" else int(product_recorded_quantity)
        product_serial_number = inspection_record["product_serial_number"]
        product_serial_number = None if product_serial_number == "無 None" else product_serial_number
        visual_inspection_result = inspection_record["visual_inspection_result"]
        visual_inspection_defect_classification = inspection_record["visual_inspection_defect_classification"]
        visual_inspection_defect_classification = None\
            if visual_inspection_defect_classification == ["none"]\
                else "/".join(visual_inspection_defect_classification)
        visual_inspection_defect_description = inspection_record["visual_inspection_defect_description"]
        visual_inspection_defect_description = None\
            if visual_inspection_defect_description == "無 None"\
                else visual_inspection_defect_description
        date_code = inspection_record["date_code"]
        date_code = None if date_code == "" else date_code
        electrical_function_inspection_result = inspection_record["electrical_function_inspection_result"]
        electrical_function_inspection_defect_classification = \
            inspection_record["electrical_function_inspection_defect_classification"]
        electrical_function_inspection_defect_classification = None\
            if electrical_function_inspection_defect_classification == ["none"]\
                else "/".join(electrical_function_inspection_defect_classification)
        electrical_function_inspection_defect_description = \
            inspection_record["electrical_function_inspection_defect_description"]
        electrical_function_inspection_defect_description = None\
            if electrical_function_inspection_defect_description == "無 None"\
                else electrical_function_inspection_defect_description
        electrical_function_inspection_value = inspection_record["electrical_function_inspection_value"]
        electrical_function_inspection_value = None\
            if electrical_function_inspection_value == ""\
                else electrical_function_inspection_value
        package_way = inspection_record["package_way"]
        package_way = None if package_way == "none" else package_way
        package_inspection_result = inspection_record["package_inspection_result"]
        package_inspection_defect_classification = \
            inspection_record["package_inspection_defect_classification"]
        package_inspection_defect_classification = None\
            if package_inspection_defect_classification == ["none"]\
                else "/".join(package_inspection_defect_classification)
        package_inspection_defect_description = inspection_record["package_inspection_defect_description"]
        package_inspection_defect_description = None\
            if package_inspection_defect_description == "無 None"\
                else package_inspection_defect_description
        inspection_result = inspection_record["inspection_result"]
        inspection_result = {"accept":1, "reject":0}[inspection_result]
        hyper_link = inspection_record["hyper_link"]
        hyper_link = None if hyper_link == "無 None" else hyper_link
        remark = inspection_record["remark"]
        remark = None if remark == "無 None" else remark
        inspector = inspection_record["inspector"]
        manager = inspection_record["manager"]
        
        new_inspection_document = inspection_record["inspection_document"]
        original_inspection_document = inspection_record["original_inspection_document"]
        new_category = inspection_record["category"]
        original_category = inspection_record["original_category"]
        inspection_document = new_inspection_document or original_inspection_document
        category = new_category or original_category
        record = Record(
                    sampling_state=sampling_state, inspection_date=inspection_date,
                    supplier_number=supplier_number,inspection_lot=inspection_lot,
                    inspection_type=inspection_type, order=order, purchasing=purchasing,
                    part_number=part_number, item_rev=item_rev, quantity=quantity,
                    inspection_quantity=inspection_quantity,major_accept=major_accept,
                    major_reject=major_reject, minor_accept=minor_accept, minor_reject=minor_reject,
                    product_recorded_quantity=product_recorded_quantity,
                    product_serial_number=product_serial_number,
                    visual_inspection_result=visual_inspection_result,
                    visual_inspection_defect_classification=visual_inspection_defect_classification,
                    visual_inspection_defect_description=visual_inspection_defect_description,
                    date_code=date_code,
                    electrical_function_inspection_result=electrical_function_inspection_result,
                    electrical_function_inspection_defect_classification=\
                        electrical_function_inspection_defect_classification,
                    electrical_function_inspection_defect_description=\
                        electrical_function_inspection_defect_description,
                    electrical_function_inspection_value=electrical_function_inspection_value,
                    package_way=package_way,
                    package_inspection_result=package_inspection_result,
                    package_inspection_defect_classification=package_inspection_defect_classification,
                    package_inspection_defect_description=package_inspection_defect_description,
                    remark=remark, inspection_result=inspection_result, hyper_link=hyper_link,
                    inspector=inspector, manager=manager
                )
        
        query_supplier = Supplier.query.filter_by(supplier_number=supplier_number).first()
        query_item = Item.query.filter_by(part_number=part_number).first()
        # 新料號存進item table
        if query_item is None:
            item_description = inspection_record["item_description"]
            item = Item(part_number=part_number, description=item_description, category=category,
                        inspection_standard=inspection_document)
            db.session.add(item)
            query_item = Item.query.filter_by(part_number=part_number).first()
        # 新廠商存進supplier table
        if query_supplier is None:
            supplier = Supplier(supplier_number=supplier_number, sampling_state=sampling_state,
                                accumulation_counts="0/0/-1")
            db.session.add(supplier)
            query_supplier = Supplier.query.filter_by(supplier_number=supplier_number).first()
        # 包裝方式為reel，檢驗量改成1，收退改成0 1
        if package_way == "reel":
            record.inspection_quantity = 1
            record.major_accept, record.major_reject = 0, 1
            record.minor_accept, record.minor_reject = 0, 1
        # 修改檢驗規範
        if new_inspection_document and new_inspection_document != original_inspection_document:
            query_item.inspection_standard = new_inspection_document
        # 修改category
        if new_category and new_category != original_category:
            query_item.category = new_category
            # Material 改成 Product, STI SKU
            # 物料改成品 --> 重算檢驗量，且成品不計算主缺次缺
            if original_category == "Material" and new_category in ["Product", "STI SKU"]:
                record.inspection_quantity = calculate_inspection_quantity_of_product(quantity)[0]
                record.major_accept = record.major_reject = record.minor_accept = record.minor_reject = None
            # Product, STI SKU 改成 Material
            # 成品改物料 --> 重算檢驗量，且抽樣狀態要改成此廠商的抽樣狀態
            elif original_category in ["Product", "STI SKU"] and new_category == "Material":
                revised_inspection_quantity = calculate_inspection_quantity(quantity=quantity,
                sampling_method=aql, sampling_state={-1:"免驗", 0:"減量", 1:"正常", 2:"加嚴"}[sampling_state])
                record.inspection_quantity, record.major_accept, record.major_reject,\
                record.minor_accept, record.minor_reject = revised_inspection_quantity
                record.sampling_state = query_supplier.sampling_state
            # Product 改成 STI SKU
            elif original_category == "Product" and new_category == "STI SKU":
                pass
            # STI SKU 改成 Product
            elif original_category == "STI SKU" and new_category == "Product":
                pass
        # 檢驗的是成品，不需要計算廠商的抽樣狀態和累積次數，把這筆檢驗的抽樣狀態設為正常
        if category in ["Product" , "STI SKU"]:
            record.sampling_state = 1
            pass
        # 檢驗的是物料，需要計算廠商抽樣狀態和累積次數的改變
        else:
            sampling_state = query_supplier.sampling_state
            accumulation_counts = query_supplier.accumulation_counts
            sampling_state_and_accumulation_counts_after_inspection =\
            calculate_sampling_state_and_accumulation_counts(result=inspection_result,\
            state=sampling_state, counts=accumulation_counts)
            revised_sampling_state, revised_accumulation_counts = sampling_state_and_accumulation_counts_after_inspection
            query_supplier.sampling_state = revised_sampling_state
            query_supplier.accumulation_counts = revised_accumulation_counts
            # 廠商的抽樣狀態從減量檢驗轉為免驗，在inspection_required_to_inspection_free_event table中存入一筆紀錄
            if sampling_state == 0 and revised_sampling_state == -1:
                time = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
                supplier_number = query_supplier.supplier_number
                supplier_name = query_supplier.supplier_name
                required_to_free = RequiredToFree(
                    time=time,
                    supplier_number=supplier_number,
                    supplier_name=supplier_name
                )
                db.session.add(required_to_free)
        # 免驗廠商的檢驗批出現reject  -->  存入一筆紀錄到inspection_free_vendor_reject_event table中
        if query_supplier.sampling_state == -1 and inspection_result == 0:
            email_notification_date = datetime.datetime.strptime(inspection_date, "%Y-%m-%d") + datetime.timedelta(days=60)
            reject = Reject(date=email_notification_date, supplier_number=supplier_number)
            db.session.add(reject)

        # 存入檢驗紀錄
        db.session.add(record)
        db.session.commit()
    return redirect(url_for("input_iqc_data"))


@app.route("/show_ending_page", methods=["POST", "GET"])
def show_ending_page():
    """
    回傳資料已寫入資料庫的訊息，並出現"繼續輸入"的按鈕
    """
    return render_template("ending_page.html")


@app.route("/continue_or_finish", methods=["POST", "GET"])
def continue_or_finish():
    """
    回傳首頁
    """
    if request.values["continue_or_finish"] == "continue":
        return redirect(url_for("home"))



if __name__ == "__main__":
    app.run()