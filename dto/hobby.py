
class Hobby:

  def __init__(self, name, eng_name):
    self.name = name
    self.eng_name = eng_name
    self.desc = None
    self.detail = None
    self.equipments = None
    self.additional_info = None

  def set_desc(self, desc):
    self.desc = desc

  def set_detail(self, detail):
    self.detail = detail

  def set_equipments(self, equipments):
    self.equipments = equipments

  def set_additional_info(self, additional_info):
    self.additional_info = additional_info

  def __repr__(self):
    # 현재 있는 속성만 딕셔너리로 가져옴
    attrs = ',\n  '.join(f"{k}: {repr(v)}" for k, v in self.__dict__.items())
    return f"Hobby(\n  {attrs}\n)"