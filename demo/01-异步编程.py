# import time
# import asyncio
#
# _background_tasks: set[asyncio.Task] = set()
#
# async def grade_exam(exam_id):
#     print(f"开始批改试卷 {exam_id}……")
#     await asyncio.sleep(2)  # 模拟耗时的批改过程
#     print(f"试卷 {exam_id} 批改完成")
#
# async def submit():
#     task = asyncio.create_task(grade_exam('EX-001'))
#     _background_tasks.add(task)
#     task.add_done_callback(_background_tasks.discard)
#     print("接口立即返回：已收到，正在后台批改")
#
# async def main():
#     await submit()
#     await asyncio.sleep(3)
#     print("当前后台任务数：", len(_background_tasks))
#
#
# asyncio.run(main())
#
# # 接口立即返回：已收到，正在后台批改
# # 开始批改试卷 EX-001……
# # 试卷 EX-001 批改完成
# # 当前后台任务数： 0

import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def fn ():
    print('开始')
    yield
    print('结束')


async def main():
    async with fn():
        print('执行')

asyncio.run(main())

