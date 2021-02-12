#!/usr/bin/env python3

import carla
import random
import logging
import time

from scipy.optimize import minimize

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

def norm_vector(vector=carla.Vector3D):
    length = (vector.x**2 + vector.y**2 + vector.z**2)**(1/2)
    return vector/length

def reward_function(distance):
    if distance != 0.0:
        reward = min(1/distance, 100)
    else:
        reward = 100
    return reward

def run_scenario(walk_dir):
    walk_x, walk_y = walk_dir
    vehicles_list = []
    walkers_list = []
    all_id = []

    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0) # seconds

    synchronous_master = False

    min_distance = 1000.0

    try:
        world = client.get_world()

        # vehicles

        traffic_manager = client.get_trafficmanager(8000)
        traffic_manager.set_global_distance_to_leading_vehicle(1)
        traffic_manager.set_random_device_seed(0)

        blueprints = world.get_blueprint_library().filter('model3')

        spawn_points = world.get_map().get_spawn_points()
        
        SpawnActor = carla.command.SpawnActor
        SetAutopilot = carla.command.SetAutopilot
        # SetVehicleLightState = carla.command.SetVehicleLightState
        FutureActor = carla.command.FutureActor

        # spawn vehicle

        blueprint = blueprints[0]
        transform = spawn_points[2]

        batch = []

        # TODO what is the driver_id used for?
        if blueprint.has_attribute('driver_id'):        
            driver_id = random.choice(blueprint.get_attribute('driver_id').recommended_values)
            blueprint.set_attribute('driver_id', driver_id)

        blueprint.set_attribute('role_name', 'autopilot')
        batch.append(SpawnActor(blueprint, transform)
            .then(SetAutopilot(FutureActor, True, traffic_manager.get_port())))

        for response in client.apply_batch_sync(batch, synchronous_master):
            if response.error:
                logging.error(response.error)
            else:
                vehicles_list.append(response.actor_id)


        # walker
        batch = []
        transform = carla.Transform(carla.Location(x=185.647888, y=15.172070, z=1.055295), carla.Rotation(pitch=1.602929, yaw=-157.672867, roll=0.000046))
        blueprintsWalkers = world.get_blueprint_library().filter('walker.pedestrian.*')

        walker_bp = random.choice(blueprintsWalkers)

        batch.append(SpawnActor(walker_bp, transform))

        results = client.apply_batch_sync(batch, True)

        walkers_list.append({"id": results[0].actor_id})

        walker_control = carla.WalkerControl()

        walker = world.get_actor(walkers_list[0]['id'])

        walker_direction = carla.Vector3D(x = walk_x, y = walk_y)

        walker.apply_control(carla.WalkerControl(
            direction = norm_vector(walker_direction), speed=1))


        # spectator

        spectator = world.get_spectator()
        spectator.set_transform(transform)

        cumulative_reward = 0.0

        
        for i in range(20):
            
            vehicle = world.get_actor(vehicles_list[0])
            vehicle_location = vehicle.get_location()
            walker_location = walker.get_location()
            distance = walker_location.distance(vehicle_location)
            logging.debug('distance: {}'.format(distance))
            min_distance = min(min_distance, distance)
            logging.debug('walking_direction: {}'.format(walker_control.direction))

            time.sleep(1)



        # time.sleep(20)
    finally:
        
        logging.info('\ndestroying %d vehicles' % len(vehicles_list))
        client.apply_batch([carla.command.DestroyActor(x) for x in vehicles_list])

        logging.info('destroying %d walkers' % len(walkers_list))
        client.apply_batch([carla.command.DestroyActor(x['id']) for x in walkers_list])

        time.sleep(0.5)
        logging.info('min_distance to vehicle: {}'.format(min_distance))
        logging.info('for walk_x: {} and walk_y: {}'.format(walk_x, walk_y))
        return min_distance

def main():
    res = minimize(run_scenario, x0=[-1.0, -1.0], bounds=((-1.0, 1.0), (-1.0, 1.0)))
    print(res)



if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        logging.info('done')