#!/usr/bin/env python3

import carla
import random
import logging
import time

def norm_vector(vector=carla.Vector3D):
    length = (vector.x**2 + vector.y**2 + vector.z**2)**(1/2)
    return vector/length

def reward_function(distance):
    if distance != 0.0:
        reward = min(1/distance, 100)
    else:
        reward = 100
    return reward

def main():
    vehicles_list = []
    walkers_list = []
    all_id = []

    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0) # seconds

    synchronous_master = False

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

        # walker controller
        batch = []
        walker_controller_bp = world.get_blueprint_library().find('controller.ai.walker')
        batch.append(SpawnActor(walker_controller_bp, carla.Transform(), walkers_list[0]["id"]))

        results = client.apply_batch_sync(batch, True)

        walkers_list[0]["con"] = results[0].actor_id

        for i in range(len(walkers_list)):
            all_id.append(walkers_list[i]["con"])
            all_id.append(walkers_list[i]["id"])
        all_actors = world.get_actors(all_id)

        world.set_pedestrians_cross_factor(1)

        for i in range(0, len(all_id), 2):
            # start walker
            all_actors[i].start()
            # set walk to random point
            all_actors[i].go_to_location(world.get_random_location_from_navigation())
            # max speed
            all_actors[i].set_max_speed(float(4))

        # spectator

        spectator = world.get_spectator()
        spectator.set_transform(transform)

        cumulative_reward = 0.0
        RUN_DISTANCE = 50

        for i in range(30):
            vehicle = world.get_actor(vehicles_list[0])
            vehicle_location = vehicle.get_location()
            vehicle_location_front = vehicle.get_transform().get_forward_vector() * 2 + vehicle_location
            walker_location = all_actors[0].get_location()
            distance = walker_location.distance(vehicle_location)
            print('distance to vehicle: {}'.format(distance))
            reward = reward_function(distance)
            cumulative_reward += reward
            print('reward: {}'.format(reward))

            if i == 0:
                all_actors[0].start()
            if distance > RUN_DISTANCE:
                # all_actors[0].start()
                all_actors[0].go_to_location(vehicle_location)
                
            elif distance <= RUN_DISTANCE:
                print('running towards the vehicle')
                
                # OW + WC = OC <=> WC = OC - OW
                
                walker_direction = vehicle_location_front - walker_location
                
                
                all_actors[0].stop()
                walker = world.get_actor(walkers_list[0]["id"])
                walker.apply_control(carla.WalkerControl(direction = norm_vector(walker_direction), speed=3))
            
            time.sleep(1)


        # time.sleep(20)
    finally:
        print('cumulative_reward: {}'.format(cumulative_reward))
        print('\ndestroying %d vehicles' % len(vehicles_list))
        client.apply_batch([carla.command.DestroyActor(x) for x in vehicles_list])

        for i in range(0, len(all_id), 2):
            all_actors[i].stop()

        print('\ndestroying %d walkers' % len(walkers_list))
        client.apply_batch([carla.command.DestroyActor(x) for x in all_id])

        time.sleep(0.5)

if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print('\ndone.')