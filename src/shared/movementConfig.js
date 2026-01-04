const fs = require("fs");
const path = require("path");

const DEFAULT_MOVEMENT_CONFIG = Object.freeze({
  maxSpeed: 320, // ups
  groundAcceleration: 10, // Quake 3 style ground accel
  airAcceleration: 15, // Quake 3 strafe-jump feel
  airControl: 2.5, // how strongly air control bends velocity toward wishdir
  friction: 6,
  stopSpeed: 100,
  gravity: 20,
  jumpSpeed: 8,
  bunnyhop: true,
  sideStrafeAccel: 50,
  sideStrafeSpeed: 30
});

function loadMovementConfig(configPath = path.join(__dirname, "../../config/movement.json")) {
  try {
    const contents = fs.readFileSync(configPath, "utf8");
    const parsed = JSON.parse(contents);
    return { ...DEFAULT_MOVEMENT_CONFIG, ...parsed };
  } catch (err) {
    return { ...DEFAULT_MOVEMENT_CONFIG };
  }
}

module.exports = {
  DEFAULT_MOVEMENT_CONFIG,
  loadMovementConfig
};
