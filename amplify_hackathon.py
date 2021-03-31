import csv

from amplify import gen_symbols, BinaryPoly, sum_poly, Solver, decode_solution
from amplify.client import FixstarsClient

for input_i in range(16):

    test_filename = 'test_data/polarization_test_observe_{:0=2}.csv'.format(input_i)

    # 探索する偏光データ入力
    with open(test_filename) as f:
        reader = csv.reader(f)
        header_param = next(reader)
        header = next(reader)
        pol_data_test = [row for row in reader]

    # 各eta, gammaでの偏光データ数値化
    for data_i in range(len(pol_data_test)):
        for data_j in range(len(pol_data_test[data_i])):
            pol_data_test[data_i][data_j] = float(pol_data_test[data_i][data_j])

    pa_test = []
    for i in range(len(pol_data_test)):
        pa_test.append([pol_data_test[i][0], pol_data_test[i][2]])

    pa_diff_test = []
    for i in range(len(pol_data_test)):
        if i < len(pol_data_test) - 1:
            angle_diff = pol_data_test[i+1][2] - pol_data_test[i][2]
            pa_diff_test.append([pol_data_test[i][0], angle_diff])
        else:
            angle_diff = pol_data_test[0][2] - pol_data_test[i][2]
            pa_diff_test.append([pol_data_test[i][0], angle_diff])

    # 偏光データ全体
    pol_data = []

    eta_num = 10
    gamma_num = 10

    for i in range(eta_num):
        for j in range(gamma_num):
            eta = 10 * i
            gamma = 10 * j

            input_filename = 'template_data/polarization_template_eta{:0=2}_gamma{:0=2}.csv'.format(eta, gamma)

            # 各eta, gammaでの偏光データ入力
            with open(input_filename) as f:
                reader = csv.reader(f)
                header = next(reader)
                pol_data_input = [row for row in reader]

            # 各eta, gammaでの偏光データ数値化
            for data_i in range(len(pol_data_input)):
                for data_j in range(len(pol_data_input[data_i])):
                    pol_data_input[data_i][data_j] = float(pol_data_input[data_i][data_j])

            # 各eta, gammaでの偏光データ整理
            pol_data.append([eta, gamma, pol_data_input])

    pa_data = []
    for i in range(len(pol_data)):
        pa_each = []

        for j in range(len(pol_data[i][2])):
            pa_each.append([pol_data[i][2][j][0], pol_data[i][2][j][2]])

        pa_data.append([pol_data[i][0], pol_data[i][1], pa_each])

    pa_diff_data = []
    for i in range(len(pol_data)):
        pa_diff_each = []

        for j in range(len(pol_data[i][2])):

            if j < len(pol_data[i][2]) - 1:
                angle_diff = pol_data[i][2][j+1][2] - pol_data[i][2][j][2]
                pa_diff_each.append([pol_data[i][2][j][0], angle_diff])
            else:
                angle_diff = pol_data[i][2][0][2] - pol_data[i][2][j][2]
                pa_diff_each.append([pol_data[i][2][j][0], angle_diff])

        pa_diff_data.append([pol_data[i][0], pol_data[i][1], pa_diff_each])


    # テンプレートとして持っているデータの個数をバイナリ変数の数とする。
    # 1のとき、その角度パラメータである。0のときその角度パラメータではないとする。
    q = gen_symbols(BinaryPoly, len(pa_diff_data))

    # onehot条件: 当てはまる角度パラメータは1つだけ
    const_onehot = (sum_poly(q) - 1) ** 2 

    # 目的関数: 各回転位相での偏光角の違いを小さくするためのもの
    obj_pa = 0.0
    coef = 1.0/180.0

    for j in range(len(pa_test)):
        obj_pa_j = pa_test[j][1]

        for i in range(len(pa_data)):
            obj_pa_j -= pa_data[i][2][j][1] * q[i]

        obj_pa += coef **2 * obj_pa_j **2

    # 目的関数: 各回転位相の偏光角の変化の違いを小さくするためのもの
    obj_pa_diff = 0.0
    coef = 1.0/180.0

    for j in range(len(pa_diff_test)):
        obj_pa_diff_j = pa_diff_test[j][1]

        for i in range(len(pa_diff_data)):
            obj_pa_diff_j -= pa_diff_data[i][2][j][1] * q[i]

        obj_pa_diff += coef **2 * obj_pa_diff_j **2

    H = 1.0 * const_onehot + 1.0 * obj_pa + 1.0 * obj_pa_diff

    # クライアントの設定
    client = FixstarsClient()
    client.parameters.timeout = 1000
    # client.token = ""

    # ソルバーの構築
    solver = Solver(client)

    # 問題を入力してマシンを実行
    result = solver.solve(H)

    # 出力
    for sol in result:
        solution = decode_solution(q, sol.values)

    count = 0
    index = -1
    for i in range(len(pa_diff_data)):
        if solution[i] == 1:
            count += 1
            index = i

    if count == 0:
        print('count = 0 !!')
    elif count > 1:
        print('count > 1 !!')

    print('estimated eta =', pa_diff_data[index][0])
    print('estimated gamma =', pa_diff_data[index][1])

    # 探索する偏光データ入力
    with open(test_filename) as f:
        reader = csv.reader(f)
        header_param = next(reader)

    print('answer eta = ', header_param[0])
    print('answer gamma = ', header_param[1])

    if abs(int(pa_diff_data[index][0]) - int(header_param[0])) <= 5 and abs(int(pa_diff_data[index][1]) - int(header_param[1])) <= 5:
        print('Correct!!')
    else:
        print('Not Correct!!')
