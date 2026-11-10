-- 复制为 hardware.lua 前，填写目标设备实际输出名和支持的模式。
-- OUTPUT_NAME 是占位符，不是可直接部署的显示器标识。
-- 多显示器时按需添加相同结构的条目，并调整 position。
-- monitor.lua 读取全部四个字段；window-management.lua 按 name 匹配，
-- 同角色存在多个匹配输出时优先采用此列表中靠前的条目。
return {
    monitors = {
        {
            name = "OUTPUT_NAME",
            mode = "1920x1080@60", -- 宽x高@刷新率；按设备能力填写
            position = "0x0",     -- 布局坐标 xxy
            scale = 1,            -- 缩放比例
        },
    },
}
