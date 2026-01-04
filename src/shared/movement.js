const { directionFromInput } = require("./protocol");
const { DEFAULT_MOVEMENT_CONFIG } = require("./movementConfig");

function normalizeDirection(dir) {
  const length = Math.hypot(dir.x, dir.y);
  if (length === 0) {
    return { x: 0, y: 0 };
  }
  return { x: dir.x / length, y: dir.y / length };
}

function applyFriction(velocity, config, deltaSeconds) {
  const speed = Math.hypot(velocity.x, velocity.y);
  if (speed <= 0) return;

  const control = speed < config.stopSpeed ? config.stopSpeed : speed;
  const drop = control * config.friction * deltaSeconds;
  const newSpeed = Math.max(speed - drop, 0);
  const scale = newSpeed / speed || 0;
  velocity.x *= scale;
  velocity.y *= scale;
}

function accelerate(velocity, wishDir, wishSpeed, accel, deltaSeconds) {
  const currentSpeed = velocity.x * wishDir.x + velocity.y * wishDir.y;
  const addSpeed = wishSpeed - currentSpeed;
  if (addSpeed <= 0) return;

  let accelSpeed = accel * wishSpeed * deltaSeconds;
  if (accelSpeed > addSpeed) {
    accelSpeed = addSpeed;
  }

  velocity.x += wishDir.x * accelSpeed;
  velocity.y += wishDir.y * accelSpeed;
}

function applyAirControl(velocity, wishDir, wishSpeed, deltaSeconds, config) {
  if (Math.abs(wishDir.x) < 0.0001 && Math.abs(wishDir.y) < 0.0001) return;
  const speed = velocity.x * wishDir.x + velocity.y * wishDir.y;
  if (speed <= 0) return;

  const controlAmount = config.airControl * speed * speed * deltaSeconds;
  velocity.x += wishDir.x * controlAmount;
  velocity.y += wishDir.y * controlAmount;

  const resultingSpeed = Math.hypot(velocity.x, velocity.y);
  if (resultingSpeed > wishSpeed && resultingSpeed > 0) {
    const scale = wishSpeed / resultingSpeed;
    velocity.x *= scale;
    velocity.y *= scale;
  }
}

function integrateMovement(previousState, input, dtMs, movementOverrides = {}) {
  const config = { ...DEFAULT_MOVEMENT_CONFIG, ...movementOverrides };
  const deltaSeconds = (dtMs || 0) / 1000;
  const state = {
    ...previousState,
    position: { ...previousState.position },
    velocity: { ...previousState.velocity },
    onGround: previousState.onGround !== undefined ? previousState.onGround : true
  };

  const wishDir = normalizeDirection(directionFromInput(input || {}));
  const wishSpeed = Math.min(config.maxSpeed, Math.hypot(wishDir.x, wishDir.y) * config.maxSpeed);

  const requestingJump = Boolean(input && input.jump);
  const skipFriction = config.bunnyhop && requestingJump;

  if (state.onGround && !skipFriction) {
    applyFriction(state.velocity, config, deltaSeconds);
  }

  if (state.onGround && requestingJump) {
    state.onGround = false;
    state.velocity.z = config.jumpSpeed;
  }

  if (state.onGround) {
    accelerate(state.velocity, wishDir, wishSpeed, config.groundAcceleration, deltaSeconds);
  } else {
    const cappedWishSpeed = wishSpeed;
    accelerate(state.velocity, wishDir, cappedWishSpeed, config.airAcceleration, deltaSeconds);

    if (!wishDir.y && wishDir.x !== 0 && config.sideStrafeAccel > 0) {
      const sideWishSpeed = Math.min(config.sideStrafeSpeed, cappedWishSpeed);
      accelerate(state.velocity, wishDir, sideWishSpeed, config.sideStrafeAccel, deltaSeconds);
    }

    if (config.airControl > 0) {
      applyAirControl(state.velocity, wishDir, cappedWishSpeed, deltaSeconds, config);
    }
  }

  state.position.x += state.velocity.x * deltaSeconds;
  state.position.y += state.velocity.y * deltaSeconds;

  state.velocity.z = (state.velocity.z || 0) - config.gravity * deltaSeconds;
  state.position.z = (state.position.z || 0) + state.velocity.z * deltaSeconds;

  if (state.position.z <= 0) {
    state.position.z = 0;
    if (state.velocity.z < 0) {
      state.velocity.z = 0;
    }
    state.onGround = true;
  }

  return state;
}

module.exports = {
  integrateMovement
};
