
import jittery_app.thing
from jittery_app.thing import a_value, add as _add
from jittery_app.thing import a_value as b_value
import jittery_app.thing as thang

if __name__ is '__main__':
  console.log(jittery_app.thing.add(1, 2))
  console.log(_add(5, 6))
  console.log(a_value)
  console.log(b_value)
  console.log(thang.a_value)
