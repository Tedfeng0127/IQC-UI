import re



def split_input_iqc_info(iqc_info):
    """
    接收使用者從前端頁面輸入的物料資訊(從HTML的textarea傳入)
    輸入格式為字串，以"\n"區分不同的rows，以"\t"區分不同的columns
    回傳分割完成的list
    """
    rows = iqc_info.split("\n")
    return_list = [i.split("\t") for i in rows if len(i) != 0]
    return return_list


def generate_inspection_standard_of_new_part_number(prefix_table, part_number=None):
    """
    當輸入新料號時(item table裡面沒有的料號)，
    根據料號的prefix產生檢驗規範和抽樣計畫
    """
    for prefix in prefix_table:
        matching_result = re.match(prefix.regex_part_number_prefix, part_number)
        if matching_result:
            inspection_standard = prefix.inspection_standard
            return inspection_standard
    inspection_standard = "QW-Q029"
    return inspection_standard


def calculate_sampling_state_and_accumulation_counts(result, state, counts:list):
    """
    根據檢驗結果、抽樣狀態、累積次數計算抽樣狀態和累積次數的變化，
    並回傳最新的抽樣狀態和累積次數

    input:
    result  -->  檢驗結果   1(accept) / 0(reject)
    state   -->  抽樣狀態   0(減量) / 1(正常) / 2(加嚴)
    counts  -->  累積次數   連續accept筆數 / 近5筆檢驗紀錄reject數 / 上一次出現reject距離現在這筆的筆數
    """
    accumulation_counts = [int(i) for i in counts.split("/")]
    consecutive_accept_number, reject_number_in_recent_five_record,\
    last_reject_record_number = accumulation_counts
    result = {1:"accept", 0:"reject"}[result]

    # 減量檢驗 且 合格
    if state == 0 and result == "accept":
        # 因為這筆合格，所以連續合格筆數+1，
        # 如果上一筆不合格距離現在的筆數不等於-1(代表之前出現過不合格的紀錄)，就+1
        consecutive_accept_number += 1
        if last_reject_record_number != -1:
            last_reject_record_number += 1
        # 如果連續合格筆數大於等於5，或上一筆不合格資料出現在5筆之前，
        # 代表近5筆檢驗紀錄(含現在檢驗的這筆)沒有出現不合格
        if consecutive_accept_number >= 5 or last_reject_record_number >= 5:
            reject_number_in_recent_five_record = 0
        # 在減量檢驗狀態下，連續合格筆數達40筆，就可以從減量檢驗轉成免驗
        # 且當抽樣狀態從減量轉為免驗時，要存入一筆紀錄到資料庫中，讓logic app可以被觸發並寄送email通知
        if consecutive_accept_number >= 40 or last_reject_record_number >= 40:
            state = -1
            consecutive_accept_number = 0

    # 減量檢驗 且 不合格
    elif state == 0 and result == "reject":
        # 出現不合格，連續合格筆數設成0
        consecutive_accept_number = 0
        last_reject_record_number = 0  # 在不合格的情況下，要先判斷這個數字的大小，去計算近5筆不合格數，計算完才能把這個數字設為0
        # reject_number_in_recent_five_record += 1
        # 減量檢驗狀態下，一筆不合格就轉成正常檢驗
        state = 1

    # 正常檢驗 且 合格
    elif state == 1 and result == "accept":
        # 合格，連續合格筆數+1，
        # 如果之前出現過不合格紀錄，上一筆不合格距離現在筆數+1
        consecutive_accept_number += 1
        if last_reject_record_number != -1:
            last_reject_record_number += 1
        # 連續合格筆數大於等於5，或上一筆不合格距離現在筆數大於等於5，
        # 代表近5筆檢驗紀錄(含現在檢驗的這筆)沒有出現不合格
        if consecutive_accept_number >= 5 or last_reject_record_number >= 5:
            reject_number_in_recent_five_record = 0
        # 連續合格筆數達到10筆
        # 從正常檢驗轉成減量檢驗
        if consecutive_accept_number >= 10:
            state = 0
            consecutive_accept_number = 0

    # 正常檢驗 且 不合格
    elif state == 1 and result == "reject":
        # 出現不合格，連續合格筆數設成0
        consecutive_accept_number = 0
        # 要把上一筆不合格距離現在筆數設成0，
        # 且近5筆不合格筆數+1
        last_reject_record_number = 0
        reject_number_in_recent_five_record += 1
        # 正常檢驗狀態下，近5筆內出現第2次不合格，就要從正常檢驗轉成加嚴檢驗，
        # 並且把上一筆不合格距離現在筆數設成0
        if last_reject_record_number <= 3 and reject_number_in_recent_five_record >= 2:
            state = 2
            last_reject_record_number = 0
            reject_number_in_recent_five_record = 0

    # 加嚴檢驗 且 合格
    elif state == 2 and result == "accept":
        # 合格，連續合格筆數+1，
        # 如果之前出現過不合格紀錄(也就是上一筆不合格距離現在筆數不等於-1)，
        # 就把上一筆不合格距離現在筆數+1
        consecutive_accept_number += 1
        if last_reject_record_number != -1:
            last_reject_record_number += 1
        # 如果連續合格筆數大於等於5，或上一筆不合格距離現在筆數大於等於5，
        # 代表近5筆檢驗紀錄(包含現在檢驗的這筆)沒有出現不合格，所以把近5筆不合格數設成0，
        # 且加嚴檢驗狀態下連續5筆合格，從加嚴檢驗轉成正常檢驗
        if consecutive_accept_number >= 5 or last_reject_record_number >= 5:
            reject_number_in_recent_five_record = 0
            state = 1
            consecutive_accept_number = 0

    # 加嚴檢驗 且 不合格
    elif state == 2 and result == "reject":
        # 出現不合格，把連續合格筆數設成0
        consecutive_accept_number = 0
        reject_number_in_recent_five_record += 1
        last_reject_record_number = 0
    
    # 免驗狀態 且 合格
    elif state == -1 and result == "accept":
        pass

    # 免驗狀態 且 不合格
    elif state == -1 and result == "reject":
        pass
    
    # 回傳結果
    return [state, "/".join([str(consecutive_accept_number),\
        str(reject_number_in_recent_five_record), str(last_reject_record_number)])]


def calculate_inspection_quantity(quantity: int, sampling_method=0, sampling_state="減量"):
    """
    根據批量(quantity)、抽樣方法(sampling_method)(major、minor)
    和抽樣狀態(sampling_state)
    計算檢驗量、major收退、minor收退。

    sampling_method=0  -->  major0.65 minor1.0
    sampling_method=1  -->  major1.0  minor2.5
    """
    # major0.65 minor1.0
    if sampling_method == 0:
        # 減量檢驗
        if sampling_state == "減量":
            if 0 < quantity <= 280:
                major_q, major_acc, major_rej = min(quantity, 8), 0, 1
            elif 280 < quantity <= 3200:
                major_q, major_acc, major_rej = 50, 1, 2
            elif 3200 < quantity <= 10000:
                major_q, major_acc, major_rej = 80, 2, 3
            elif 10000 < quantity <= 35000:
                major_q, major_acc, major_rej = 125, 3, 4
            elif 35000 < quantity <= 150000:
                major_q, major_acc, major_rej = 200, 5, 6
            elif 150000 < quantity <= 500000:
                major_q, major_acc, major_rej = 315, 6, 7
            else:
                major_q, major_acc, major_rej = 500, 8, 9
            if 0 < quantity <= 150:
                minor_acc, minor_rej = 0, 1
            elif 150 < quantity <= 1200:
                minor_acc, minor_rej = 1, 2
            elif 1200 < quantity <= 3200:
                minor_acc, minor_rej = 2, 3
            elif 3200 < quantity <= 10000:
                minor_acc, minor_rej = 3, 4
            elif 10000 < quantity <= 35000:
                minor_acc, minor_rej = 5, 6
            elif 35000 < quantity <= 150000:
                minor_acc, minor_rej = 6, 7
            elif 150000 < quantity <= 500000:
                minor_acc, minor_rej = 8, 9
            else:
                minor_acc, minor_rej = 10, 11
        
        # 正常檢驗
        elif sampling_state == "正常" or sampling_state == "免驗" or sampling_state == "":
            if 0 < quantity <= 280:
                major_q, major_acc, major_rej = min(quantity, 20), 0, 1
            elif 280 < quantity <= 1200:
                major_q, major_acc, major_rej = 80, 1, 2
            elif 1200 < quantity <= 3200:
                major_q, major_acc, major_rej = 125, 2, 3
            elif 3200 < quantity <= 10000:
                major_q, major_acc, major_rej = 200, 3, 4
            elif 10000 < quantity <= 35000:
                major_q, major_acc, major_rej = 315, 5, 6
            elif 35000 < quantity <= 150000:
                major_q, major_acc, major_rej = 500, 7, 8
            elif 150000 < quantity <= 500000:
                major_q, major_acc, major_rej = 800, 10, 11
            else:
                major_q, major_acc, major_rej = 1250, 14, 15
            if 0 < quantity <= 150:
                minor_acc, minor_rej = 0, 1
            elif 150 < quantity <= 500:
                minor_acc, minor_rej = 1, 2
            elif 500 < quantity <= 1200:
                minor_acc, minor_rej = 2, 3
            elif 1200 < quantity <= 3200:
                minor_acc, minor_rej = 3, 4
            elif 3200 < quantity <= 10000:
                minor_acc, minor_rej = 5, 6
            elif 10000 < quantity <= 35000:
                minor_acc, minor_rej = 7, 8
            elif 35000 < quantity <= 150000:
                minor_acc, minor_rej = 10, 11
            elif 150000 < quantity <= 500000:
                minor_acc, minor_rej = 14, 15
            else:
                minor_acc, minor_rej = 21, 22
            
        # 加嚴檢驗
        else:
            if 0 < quantity <= 280:
                major_q, major_acc, major_rej = min(quantity, 32), 0, 1
            elif 280 < quantity <= 3200:
                major_q, major_acc, major_rej = 125, 1, 2
            elif 3200 < quantity <= 10000:
                major_q, major_acc, major_rej = 200, 2, 3
            elif 10000 < quantity <= 35000:
                major_q, major_acc, major_rej = 315, 3, 4
            elif 35000 < quantity <= 150000:
                major_q, major_acc, major_rej = 500, 5, 6
            elif 150000 < quantity <= 500000:
                major_q, major_acc, major_rej = 800, 8, 9
            else:
                major_q, major_acc, major_rej = 1250, 12, 13
            if 0 < quantity <= 150:
                minor_acc, minor_rej = 0, 1
            elif 150 < quantity <= 1200:
                minor_acc, minor_rej = 1, 2
            elif 1200 < quantity <= 3200:
                minor_acc, minor_rej = 2, 3
            elif 3200 < quantity <= 10000:
                minor_acc, minor_rej = 3, 4
            elif 10000 < quantity <= 35000:
                minor_acc, minor_rej = 5, 6
            elif 35000 < quantity <= 150000:
                minor_acc, minor_rej = 8, 9
            elif 150000 < quantity <= 500000:
                minor_acc, minor_rej = 12, 13
            else:
                minor_acc, minor_rej = 18, 19
    
    # major1.0 minor2.5
    else:
        # 減量檢驗
        if sampling_state == "減量":
            if 0 < quantity <= 150:
                major_q, major_acc, major_rej = min(quantity, 5), 0, 1
            elif 150 < quantity <= 1200:
                major_q, major_acc, major_rej = 32, 1, 2
            elif 1200 < quantity <= 3200:
                major_q, major_acc, major_rej = 50, 2, 3
            elif 3200 < quantity <= 10000:
                major_q, major_acc, major_rej = 80, 3, 4
            elif 10000 < quantity <= 35000:
                major_q, major_acc, major_rej = 125, 5, 6
            elif 35000 < quantity <= 150000:
                major_q, major_acc, major_rej = 200, 6, 7
            elif 150000 < quantity <= 500000:
                major_q, major_acc, major_rej = 315, 8, 9
            else:
                major_q, major_acc, major_rej = 500, 10, 11
            if 0 < quantity <= 50:
                minor_acc, minor_rej = 0, 1
            elif 50 < quantity <= 280:
                minor_acc, minor_rej = 1, 2
            elif 280 < quantity <= 500:
                minor_acc, minor_rej = 2, 3
            elif 500 < quantity <= 1200:
                minor_acc, minor_rej = 3, 4
            elif 1200 < quantity <= 3200:
                minor_acc, minor_rej = 5, 6
            elif 3200 < quantity <= 10000:
                minor_acc, minor_rej = 6, 7
            elif 10000 < quantity <= 35000:
                minor_acc, minor_rej = 8, 9
            else:
                minor_acc, minor_rej = 10, 11

        # 正常檢驗
        elif sampling_state == "正常" or sampling_state == "免驗" or sampling_state == "":
            if 0 < quantity <= 150:
                major_q, major_acc, major_rej = min(quantity, 13), 0, 1
            elif 150 < quantity <= 500:
                major_q, major_acc, major_rej = 50, 1, 2
            elif 500 < quantity <= 1200:
                major_q, major_acc, major_rej = 80, 2, 3
            elif 1200 < quantity <= 3200:
                major_q, major_acc, major_rej = 125, 3, 4
            elif 3200 < quantity <= 10000:
                major_q, major_acc, major_rej = 200, 5, 6
            elif 10000 < quantity <= 35000:
                major_q, major_acc, major_rej = 315, 7, 8
            elif 35000 < quantity <= 150000:
                major_q, major_acc, major_rej = 500, 10, 11
            elif 150000 < quantity <= 500000:
                major_q, major_acc, major_rej = 800, 14, 15
            else:
                major_q, major_acc, major_rej = 1250, 21, 22
            if 0 < quantity <= 50:
                minor_acc, minor_rej = 0, 1
            elif 50 < quantity <= 150:
                minor_acc, minor_rej = 1, 2
            elif 150 < quantity <= 280:
                minor_acc, minor_rej = 2, 3
            elif 280 < quantity <= 500:
                minor_acc, minor_rej = 3, 4
            elif 500 < quantity <= 1200:
                minor_acc, minor_rej = 5, 6
            elif 1200 < quantity <= 3200:
                minor_acc, minor_rej = 7, 8
            elif 3200 < quantity <= 10000:
                minor_acc, minor_rej = 10, 11
            elif 10000 < quantity <= 35000:
                minor_acc, minor_rej = 14, 15
            else:
                minor_acc, minor_rej = 21, 22
        
        # 加嚴檢驗
        else:
            if 0 < quantity <= 150:
                major_q, major_acc, major_rej = min(quantity, 20), 0, 1
            elif 150 < quantity <= 1200:
                major_q, major_acc, major_rej = 80, 1, 2
            elif 1200 < quantity <= 3200:
                major_q, major_acc, major_rej = 125, 2, 3
            elif 3200 < quantity <= 10000:
                major_q, major_acc, major_rej = 200, 3, 4
            elif 10000 < quantity <= 35000:
                major_q, major_acc, major_rej = 315, 5, 6
            elif 35000 < quantity <= 150000:
                major_q, major_acc, major_rej = 500, 8, 9
            elif 150000 < quantity <= 500000:
                major_q, major_acc, major_rej = 800, 12, 13
            else:
                major_q, major_acc, major_rej = 1250, 18, 19
            if 0 < quantity <= 50:
                minor_acc, minor_rej = 0, 1
            elif 50 < quantity <= 280:
                minor_acc, minor_rej = 1, 2
            elif 280 < quantity <= 500:
                minor_acc, minor_rej = 2, 3
            elif 500 < quantity <= 1200:
                minor_acc, minor_rej = 3, 4
            elif 1200 < quantity <= 3200:
                minor_acc, minor_rej = 5, 6
            elif 3200 < quantity <= 10000:
                minor_acc, minor_rej = 8, 9
            elif 10000 < quantity <= 35000:
                minor_acc, minor_rej = 12, 13
            else:
                minor_acc, minor_rej = 18, 19
    return [major_q, major_acc, major_rej, minor_acc, minor_rej]


def calculate_inspection_quantity_of_product(quantity: int):
    """
    計算進貨的成品的檢驗量(成品和進料不同，不需要計算major minor，只需要計算檢驗量)
    """
    if 0 < quantity <= 20:
        inspection_quantity = 1
    elif 20 < quantity <= 50:
        inspection_quantity = 2
    elif 50 < quantity <= 100:
        inspection_quantity = 3
    elif 100 < quantity <= 300:
        inspection_quantity = 5
    elif 300 < quantity <= 500:
        inspection_quantity = 7
    else:
        inspection_quantity = 10
    return [inspection_quantity, "", "", "", ""]