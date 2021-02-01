#!/usr/bin/env python3

import carla
import random
import logging
import time

def main():
    vehicles_list = []

    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0) # seconds

    synchronous_master = False

    try:
        world = client.get_world()

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

        spectator = world.get_spectator()
        spectator.set_transform(transform)

        time.sleep(20)
    finally:
        print('\ndestroying %d vehicles' % len(vehicles_list))
        client.apply_batch([carla.command.DestroyActor(x) for x in vehicles_list])

        time.sleep(0.5)

if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print('\ndone.')