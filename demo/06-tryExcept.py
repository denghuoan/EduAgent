# def divide(a, b):
#     try:
#         res = a / b
#         print(f'结果:{res}')
#     except ZeroDivisionError:
#         print('division by zero')
#     except TypeError:
#         print('格式错误')
#         # raise # 报红

# divide(10, 2)
# divide(10,0)
# divide(10,'a')

# def divide(a, b):
#     try:
#         res = a / b
#         print(f'结果:{res}')
#     except (ZeroDivisionError, TypeError):
#         print('格式错误')
#
#
# divide(10,0)

times = 3
for attempt in range(times):
    try:
        print(f'第{attempt + 1}次尝试')
        if attempt < times - 1:
            raise ConnectionError('连接失败') # 前两次(attempt=0、1)故意失败
        print('成功')
    except ConnectionError as e:
        print(f"  出错: {e},继续下一次")
