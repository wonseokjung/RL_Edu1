import gym
from gym import wrappers
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import os

def qlearning_alpha_noise(env, n_episodes=2000, gamma=0.99, alpha=0.85, best_enabled=False):
    nS = env.observation_space.n
    nA = env.action_space.n

    print("Q space initialized: {} x {}".format(nS, nA))

    Q = np.zeros([nS, nA])

    if best_enabled:
        # record your best-tuned hyperparams here
        env.seed(0)
        np.random.seed(0)
        alpha = 0.05
        gamma = 0.99
        # also check the modify_reward fn

    # policy: pi(state) -> prob. distribution of actions
    policy = make_decay_noisy_policy(Q, nA)
    reward_per_episode = np.zeros(n_episodes)

    for i in range(n_episodes):
        # useful for debugging
        log_episode(i, n_episodes)

        s = env.reset()
        done = False
        total_reward = 0

        while not done:
            # Choose action by noisy probs
            if best_enabled:
                probs = policy(s, (i/10 + 1.0))
            else:
                probs = policy(s, i + 1.0)
            a = np.random.choice(np.arange(nA), p=probs)

            # take a step
            next_s, r, done, _ = env.step(a)

            if best_enabled:
                mod_r = modify_reward(r, done)
                td_target = mod_r + gamma * np.max(Q[next_s, :])
            else:
                td_target = r + gamma * np.max(Q[next_s, :])

            td_delta = td_target - Q[s, a]
            Q[s, a] += alpha * td_delta

            s = next_s
            total_reward += r

        reward_per_episode[i] = total_reward
    return Q, reward_per_episode

def make_decay_noisy_policy(Q, nA):
    def policy_fn(state, decaying_factor):
        noise = np.random.randn(1, nA) / decaying_factor
        # don't manually break ties as being of equal values is unlikely
        dist = Q[state, :]
        best_action = np.argmax(dist + noise)
        # make the policy deterministic as per argmax
        return np.eye(nA, dtype=float)[best_action]
    return policy_fn


def modify_reward(reward, done):
    # arbitrary scaling factors
    if done and reward == 0:
        return -100.0
    elif done:
        return 50.0
    else:
        return -1.0


def log_episode(i_epi, n_epi):
    if (i_epi + 1) % 100 == 0:
        print("\rEpisode {}/{}.".format(i_epi + 1, n_epi), end="")
        sys.stdout.flush()


def is_solved(stats):
    """
    checks if openai's criteria has been met
    """
    TARGET_AVG_REWARD = 0.78
    TARGET_EPISODE_INTERVAL = 100

    # FrozenLake-v0 is considered "solved" when the agent
    # obtains an average reward of at least 0.78 over 100
    # consecutive episodes.

    def moving_avg(x, n=100):
        return np.convolve(x, np.ones((n,))/n, mode='valid')

    ma = moving_avg(stats, TARGET_EPISODE_INTERVAL)
    peaks = np.where(ma > TARGET_AVG_REWARD)[0]
    if len(peaks) > 0:
        print("solved after {} episodes".format(peaks[0]))
        return True
    else:
        print("did not pass the openai criteria")
        return False


def visualize(Q, stats, output_title="output.png"):
    print("Success rate : {}".format(np.sum(stats)/len(stats)))
    print("Final Q-Table Values")
    print(Q)
    plt.figure(figsize=(8,12))
    plt.title("Reward_per_episode")
    plt.plot(stats)
    plt.xlabel("Episode")
    plt.ylabel("Reward")
    plt.savefig(output_title)

if __name__ == "__main__":
    env = gym.make('FrozenLake-v0')
    env = wrappers.Monitor(env, '/tmp/frozenlake-experiment-0', force=True)
    Q, stats = qlearning_alpha_noise(env, best_enabled=True)

    env.close()
    if is_solved(stats):
        OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
        gym.upload('/tmp/frozenlake-experiment-0', api_key=OPENAI_API_KEY)

    visualize(Q, stats, "qlearning_alpha_e_greedy.png")

