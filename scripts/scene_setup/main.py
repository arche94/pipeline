import hou

def start():
  x_shift = 3
  y_shift = -3

  root = hou.node('/obj')
  
  # backdrop setup
  geoBox = root.createNetworkBox()
  geoBox.setComment('GEOMETRY')
  geoBox.setColor(hou.Color((0.470882, 0.808387, 0.200114)))

  fxBox = root.createNetworkBox()
  fxBox.setComment('FX')
  fxBox.setColor(hou.Color((0.996771, 0, 0)))
  fxBox.setPosition((x_shift, 0))

  rndrBox = root.createNetworkBox()
  rndrBox.setComment('RENDER')
  rndrBox.setColor(hou.Color((0.317835, 0.25505, 0.57684)))
  rndrBox.setPosition((2 * x_shift, 0))
  
  camBox = root.createNetworkBox()
  camBox.setComment('CAMERAS')
  camBox.setColor(hou.Color((0.286442, 0.561143, 0.882955)))
  camBox.setPosition((3 * x_shift, 0))

  lgtBox = root.createNetworkBox()
  lgtBox.setComment('LIGHTS')
  lgtBox.setColor(hou.Color((0.996771, 0.722047, 0)))
  lgtBox.setPosition((3 * x_shift, y_shift))

  netBox = root.createNetworkBox()
  netBox.setComment('NETWORKS')
  netBox.setColor(hou.Color((0, 0, 0)))
  netBox.setPosition((4 * x_shift, 0))

  # network nodes setup
  topPos = netBox.position()
  topPos[0] += 1
  topPos[1] += 1.5
  y_shift_node = -1

  scdtaNode = root.createNode('arche_scene_data')
  scdtaNode.setPosition(topPos)
  netBox.addItem(scdtaNode)

  matNode = root.createNode('matnet')
  topPos[1] += y_shift_node
  matNode.setPosition(topPos)
  netBox.addItem(matNode)

  ropNode = root.createNode('ropnet')
  topPos[1] += 0.75 * y_shift_node
  ropNode.setPosition(topPos)
  netBox.addItem(ropNode)

  lopNode = root.createNode('lopnet')
  topPos[1] += 0.75 * y_shift_node
  lopNode.setPosition(topPos)
  netBox.addItem(lopNode)

  topNode = root.createNode('topnet')
  topPos[1] += 0.75 * y_shift_node
  topNode.setPosition(topPos)
  netBox.addItem(topNode)
  
  # adjust network backdrop
  netBoxSize = netBox.size()
  netBoxSize[0] *= 1.25
  netBox.setSize(netBoxSize)