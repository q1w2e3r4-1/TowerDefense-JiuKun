import json

class MonsterAttributeChecker:
    # 允许的选项
    ATK_SPD = {"Fast", "Normal", "Slow"}
    ELEMENTS = {"Fire", "Ice", "Poison", "Blunt", "Lightning"}
    SLOW_EFF = {"Resist", "Normal", "Weak"}
    OCCURRENCE = {"Single", "Double", "Triple", "Sparse", "Dense"}

    REQUIRED_KEYS = [
        "best_atk_spd", "weak", "resist", "special_eff", "slow_eff", "occurrence"
    ]

    def check(self, result):
        # 支持字符串和字典输入
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except Exception:
                return False, "返回内容不是合法JSON"
        # 检查字段完整性
        if set(result.keys()) != set(self.REQUIRED_KEYS):
            return False, f"字段不完整或多余，必须为{self.REQUIRED_KEYS}"
        # 检查 best_atk_spd
        if not self._check_list(result["best_atk_spd"], self.ATK_SPD, 1):
            return False, "best_atk_spd 必须为['Fast'], ['Normal']或['Slow']"
        # 检查 weak
        if not self._check_list(result["weak"], self.ELEMENTS):
            return False, "weak 必须为属性集合"
        # 检查 resist
        if not self._check_list(result["resist"], self.ELEMENTS):
            return False, "resist 必须为属性集合"
        # 检查 weak 和 resist 不重合
        if set(result["weak"]) & set(result["resist"]):
            return False, "weak 和 resist 不能有重合元素"
        # 检查 special_eff
        if not self._check_list(result["special_eff"], self.ELEMENTS, allow_empty=True):
            return False, "special_eff 必须为属性或空"
        if set(result["special_eff"]) & set(result["resist"]):
            return False, "special_eff 和 resist 不能有重合元素"
        # 检查 slow_eff
        if not self._check_list(result["slow_eff"], self.SLOW_EFF, 1):
            return False, "slow_eff 必须为['Resist'], ['Normal']或['Weak']"
        # 检查 occurrence
        if not self._check_list(result["occurrence"], self.OCCURRENCE, 1):
            return False, "occurrence 必须为['Single'], ['Double'], ['Triple'], ['Sparse']或['Dense']"
        return True, "校验通过"

    def _check_list(self, value, allowed, length=None, allow_empty=False):
        if not isinstance(value, list):
            return False
        if length is not None and len(value) != length:
            return False
        if not allow_empty and len(value) == 0:
            return False
        for v in value:
            if v not in allowed:
                return False
        return True